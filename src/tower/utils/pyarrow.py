from typing import Any, Optional, List

import pyarrow as pa
import pyarrow.compute as pc

import pyiceberg.types as types
from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.expressions import (
    BooleanExpression,
    And, Or, Not,
    EqualTo, NotEqualTo,
    GreaterThan, GreaterThanOrEqual,
    LessThan, LessThanOrEqual,
    Literal, Reference
)

def arrow_to_iceberg_type(arrow_type):
    """
    Convert a PyArrow type to a PyIceberg type. Special thanks to Claude for
    the help on this.
    """
    
    if pa.types.is_boolean(arrow_type):
        return types.BooleanType()
    elif pa.types.is_integer(arrow_type):
        # Check the bit width to determine the appropriate Iceberg integer type
        bit_width = arrow_type.bit_width
        if bit_width <= 32:
            return types.IntegerType()
        else:
            return types.LongType()
    elif pa.types.is_floating(arrow_type):
        if arrow_type.bit_width == 32:
            return types.FloatType()
        else:
            return types.DoubleType()
    elif pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return types.StringType()
    elif pa.types.is_binary(arrow_type) or pa.types.is_large_binary(arrow_type):
        return types.BinaryType()
    elif pa.types.is_date(arrow_type):
        return types.DateType()
    elif pa.types.is_timestamp(arrow_type):
        return types.TimestampType()
    elif pa.types.is_time(arrow_type):
        return types.TimeType()
    elif pa.types.is_decimal(arrow_type):
        precision = arrow_type.precision
        scale = arrow_type.scale
        return types.DecimalType(precision, scale)
    elif pa.types.is_list(arrow_type):
        element_type = arrow_to_iceberg_type(arrow_type.value_type)
        return types.ListType(element_type)
    elif pa.types.is_struct(arrow_type):
        fields = []
        for i, field in enumerate(arrow_type):
            name = field.name
            field_type = arrow_to_iceberg_type(field.type)
            fields.append(types.NestedField(i + 1, name, field_type, required=not field.nullable))
        return types.StructType(*fields)
    elif pa.types.is_map(arrow_type):
        key_type = arrow_to_iceberg_type(arrow_type.key_type)
        value_type = arrow_to_iceberg_type(arrow_type.item_type)
        return types.MapType(key_type, value_type)
    else:
        raise ValueError(f"Unsupported Arrow type: {arrow_type}")


def convert_pyarrow_field(num, field) -> types.NestedField:
    name = field.name
    field_type = arrow_to_iceberg_type(field.type)
    field_id = num + 1  # Iceberg requires field IDs

    return types.NestedField(
        field_id,
        name,
        field_type,
        required=not field.nullable
    )


def convert_pyarrow_schema(arrow_schema: pa.Schema) -> IcebergSchema:
    """Convert a PyArrow schema to a PyIceberg schema."""
    fields = [convert_pyarrow_field(i, field) for i, field in enumerate(arrow_schema)]
    return IcebergSchema(*fields)


def extract_field_and_literal(expr: pc.Expression) -> tuple[str, Any]:
    """Extract field name and literal value from a comparison expression."""
    # First, convert the expression to a string and parse it
    expr_str = str(expr)
    
    # PyArrow expression strings look like: "(field_name == literal)" or similar
    # Need to determine the operator and then split accordingly
    operators = ["==", "!=", ">", ">=", "<", "<="]
    op_used = None
    for op in operators:
        if op in expr_str:
            op_used = op
            break
    
    if not op_used:
        raise ValueError(f"Could not find comparison operator in expression: {expr_str}")
    
    # Remove parentheses and split by operator
    expr_clean = expr_str.strip("()")
    parts = expr_clean.split(op_used)
    if len(parts) != 2:
        raise ValueError(f"Expected binary comparison in expression: {expr_str}")
    
    # Determine which part is the field and which is the literal
    field_name = None
    literal_value = None
    
    # Clean up the parts
    left = parts[0].strip()
    right = parts[1].strip()
    
    # Typically field name doesn't have quotes, literals (strings) do
    if left.startswith('"') or left.startswith("'"):
        # Right side is the field
        field_name = right
        # Extract the literal value - this is a simplification
        literal_value = left.strip('"\'')
    else:
        # Left side is the field
        field_name = left
        # Extract the literal value - this is a simplification
        literal_value = right.strip('"\'')
    
    # Try to convert numeric literals
    try:
        if "." in literal_value:
            literal_value = float(literal_value)
        else:
            literal_value = int(literal_value)
    except ValueError:
        # Keep as string if not numeric
        pass
        
    return field_name, literal_value

def convert_pyarrow_expression(expr: pc.Expression) -> Optional[BooleanExpression]:
    """Convert a PyArrow compute expression to a PyIceberg boolean expression."""
    if expr is None:
        return None
    
    # Handle the expression based on its string representation
    expr_str = str(expr)
    
    # Handle logical operations
    if "and" in expr_str.lower() and isinstance(expr, pc.Expression):
        # This is a simplification - in real code, you'd need to parse the expression
        # to extract the sub-expressions properly
        left_expr = None  # You'd need to extract this
        right_expr = None  # You'd need to extract this
        return And(
            convert_pyarrow_expression(left_expr),
            convert_pyarrow_expression(right_expr)
        )
    elif "or" in expr_str.lower() and isinstance(expr, pc.Expression):
        # Similar simplification
        left_expr = None  # You'd need to extract this
        right_expr = None  # You'd need to extract this
        return Or(
            convert_pyarrow_expression(left_expr),
            convert_pyarrow_expression(right_expr)
        )
    elif "not" in expr_str.lower() and isinstance(expr, pc.Expression):
        # Similar simplification
        inner_expr = None  # You'd need to extract this
        return Not(convert_pyarrow_expression(inner_expr))
    
    # Handle comparison operations
    try:
        if "==" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return EqualTo(Reference(field_name), value)
        elif "!=" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return NotEqualTo(Reference(field_name), value)
        elif ">=" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return GreaterThanOrEqual(Reference(field_name), value)
        elif ">" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return GreaterThan(Reference(field_name), value)
        elif "<=" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return LessThanOrEqual(Reference(field_name), value)
        elif "<" in expr_str:
            field_name, value = extract_field_and_literal(expr)
            return LessThan(Reference(field_name), value)
        else:
            raise ValueError(f"Unsupported expression: {expr_str}")
    except Exception as e:
        raise ValueError(f"Failed to convert expression '{expr_str}': {str(e)}")


def convert_pyarrow_expressions(exprs: List[pc.Expression]) -> BooleanExpression:
    """
    Convert a list of PyArrow expressions to a single PyIceberg expression.
    Multiple expressions are combined with AND.
    """
    if not exprs:
        raise ValueError("No expressions provided")
    
    if len(exprs) == 1:
        return convert_pyarrow_expression(exprs[0])
    
    # Combine multiple expressions with AND
    result = convert_pyarrow_expression(exprs[0])
    for expr in exprs[1:]:
        result = And(result, convert_pyarrow_expression(expr))
    
    return result
