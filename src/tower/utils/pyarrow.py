from typing import Any, Optional, List

import pyarrow as pa
import pyarrow.compute as pc

from pyiceberg import types as iceberg_types
from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.expressions import (
    BooleanExpression,
    And,
    Or,
    Not,
    EqualTo,
    NotEqualTo,
    GreaterThan,
    GreaterThanOrEqual,
    LessThan,
    LessThanOrEqual,
    Reference,
)


class FieldIdManager:
    """
    Manages the assignment of unique field IDs.
    Field IDs in Iceberg start from 1.
    """

    def __init__(self, start_id=1):
        # Initialize current_id to start_id - 1 so the first call to get_next_id() returns start_id
        self.current_id = start_id - 1

    def get_next_id(self) -> int:
        """Returns the next available unique field ID."""
        self.current_id += 1
        return self.current_id


def arrow_to_iceberg_type_recursive(
    arrow_type: pa.DataType, field_id_manager: FieldIdManager
) -> iceberg_types.IcebergType:
    """
    Recursively convert a PyArrow DataType to a PyIceberg type,
    managing field IDs for nested structures.
    """
    # Primitive type mappings (most remain the same)
    if pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return iceberg_types.StringType()
    elif pa.types.is_integer(arrow_type):
        if arrow_type.bit_width <= 32:  # type: ignore
            return iceberg_types.IntegerType()
        else:
            return iceberg_types.LongType()
    elif pa.types.is_floating(arrow_type):
        if arrow_type.bit_width <= 32:  # type: ignore
            return iceberg_types.FloatType()
        else:
            return iceberg_types.DoubleType()
    elif pa.types.is_boolean(arrow_type):
        return iceberg_types.BooleanType()
    elif pa.types.is_date(arrow_type):
        return iceberg_types.DateType()
    elif pa.types.is_time(arrow_type):
        return iceberg_types.TimeType()
    elif pa.types.is_timestamp(arrow_type):
        if arrow_type.tz is not None:  # type: ignore
            return iceberg_types.TimestamptzType()
        else:
            return iceberg_types.TimestampType()
    elif pa.types.is_binary(arrow_type) or pa.types.is_large_binary(arrow_type):
        return iceberg_types.BinaryType()
    elif pa.types.is_fixed_size_binary(arrow_type):
        return iceberg_types.FixedType(length=arrow_type.byte_width)  # type: ignore
    elif pa.types.is_decimal(arrow_type):
        return iceberg_types.DecimalType(arrow_type.precision, arrow_type.scale)  # type: ignore

    # Nested type mappings
    elif (
        pa.types.is_list(arrow_type)
        or pa.types.is_large_list(arrow_type)
        or pa.types.is_fixed_size_list(arrow_type)
    ):
        # The element field itself in Iceberg needs an ID.
        element_id = field_id_manager.get_next_id()

        # Recursively convert the list's element type.
        # arrow_type.value_type is the DataType of the elements.
        # arrow_type.value_field is the Field of the elements (contains name, type, nullability).
        element_pyarrow_type = arrow_type.value_type  # type: ignore
        element_iceberg_type = arrow_to_iceberg_type_recursive(
            element_pyarrow_type, field_id_manager
        )

        # Determine if the elements themselves are required (not nullable).
        element_is_required = not arrow_type.value_field.nullable  # type: ignore

        return iceberg_types.ListType(
            element_id=element_id,
            element_type=element_iceberg_type,
            element_required=element_is_required,
        )
    elif pa.types.is_struct(arrow_type):
        struct_iceberg_fields = []
        # arrow_type is a StructType. Iterate through its fields.
        for i in range(arrow_type.num_fields):  # type: ignore
            pyarrow_child_field = arrow_type.field(i)  # This is a pyarrow.Field

            # Each field within the struct needs its own unique ID.
            nested_field_id = field_id_manager.get_next_id()
            nested_iceberg_type = arrow_to_iceberg_type_recursive(
                pyarrow_child_field.type, field_id_manager
            )

            doc = None
            if pyarrow_child_field.metadata and b"doc" in pyarrow_child_field.metadata:
                doc = pyarrow_child_field.metadata[b"doc"].decode("utf-8")

            struct_iceberg_fields.append(
                iceberg_types.NestedField(
                    field_id=nested_field_id,
                    name=pyarrow_child_field.name,
                    field_type=nested_iceberg_type,
                    required=not pyarrow_child_field.nullable,
                    doc=doc,
                )
            )
        return iceberg_types.StructType(*struct_iceberg_fields)
    elif pa.types.is_map(arrow_type):
        # Iceberg MapType requires IDs for key and value fields.
        key_id = field_id_manager.get_next_id()
        value_id = field_id_manager.get_next_id()

        key_iceberg_type = arrow_to_iceberg_type_recursive(
            arrow_type.key_type, field_id_manager
        )  # type: ignore
        value_iceberg_type = arrow_to_iceberg_type_recursive(
            arrow_type.item_type, field_id_manager
        )  # type: ignore

        # PyArrow map keys are always non-nullable by Arrow specification.
        # Nullability of map values comes from the item_field.
        value_is_required = not arrow_type.item_field.nullable  # type: ignore

        return iceberg_types.MapType(
            key_id=key_id,
            key_type=key_iceberg_type,
            value_id=value_id,
            value_type=value_iceberg_type,
            value_required=value_is_required,
        )
    else:
        raise ValueError(f"Unsupported Arrow type: {arrow_type}")


def convert_pyarrow_schema(
    arrow_schema: pa.Schema, schema_id: int = 1, start_field_id: int = 1
) -> IcebergSchema:
    """
    Convert a PyArrow schema to a PyIceberg schema.

    Args:
        arrow_schema: The input PyArrow.Schema.
        schema_id: The schema ID for the Iceberg schema.
        start_field_id: The starting ID for field ID assignment.
    Returns:
        An IcebergSchema object.
    """
    field_id_manager = FieldIdManager(start_id=start_field_id)
    iceberg_fields = []

    for pyarrow_field in arrow_schema:  # pyarrow_field is a pa.Field object
        # Assign a unique ID for this top-level field.
        top_level_field_id = field_id_manager.get_next_id()

        # Recursively convert the field's type. This will handle ID assignment
        # for any nested structures using the same field_id_manager.
        iceberg_field_type = arrow_to_iceberg_type_recursive(
            pyarrow_field.type, field_id_manager
        )

        doc = None
        if pyarrow_field.metadata and b"doc" in pyarrow_field.metadata:
            doc = pyarrow_field.metadata[b"doc"].decode("utf-8")

        iceberg_fields.append(
            iceberg_types.NestedField(
                field_id=top_level_field_id,
                name=pyarrow_field.name,
                field_type=iceberg_field_type,
                required=not pyarrow_field.nullable,  # Top-level field nullability
                doc=doc,
            )
        )
    return IcebergSchema(*iceberg_fields, schema_id=schema_id)


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
        raise ValueError(
            f"Could not find comparison operator in expression: {expr_str}"
        )

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
        literal_value = left.strip("\"'")
    else:
        # Left side is the field
        field_name = left
        # Extract the literal value - this is a simplification
        literal_value = right.strip("\"'")

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
            convert_pyarrow_expression(right_expr),
        )
    elif "or" in expr_str.lower() and isinstance(expr, pc.Expression):
        # Similar simplification
        left_expr = None  # You'd need to extract this
        right_expr = None  # You'd need to extract this
        return Or(
            convert_pyarrow_expression(left_expr),
            convert_pyarrow_expression(right_expr),
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
