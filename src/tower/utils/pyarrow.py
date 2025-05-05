from typing import Optional, List

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


def iceberg_to_arrow_type(iceberg_type):
    """
    Convert a PyIceberg type to a PyArrow type.
    """
    if isinstance(iceberg_type, types.BooleanType):
        return pa.bool_()
    elif isinstance(iceberg_type, types.IntegerType):
        return pa.int32()
    elif isinstance(iceberg_type, types.LongType):
        return pa.int64()
    elif isinstance(iceberg_type, types.FloatType):
        return pa.float32()
    elif isinstance(iceberg_type, types.DoubleType):
        return pa.float64()
    elif isinstance(iceberg_type, types.StringType):
        return pa.string()
    elif isinstance(iceberg_type, types.BinaryType):
        return pa.binary()
    elif isinstance(iceberg_type, types.DateType):
        return pa.date32()
    elif isinstance(iceberg_type, types.TimestampType):
        # Using microsecond precision as default
        return pa.timestamp('us')
    elif isinstance(iceberg_type, types.TimeType):
        # Using microsecond precision as default
        return pa.time64('us')
    elif isinstance(iceberg_type, types.DecimalType):
        return pa.decimal128(iceberg_type.precision, iceberg_type.scale)
    elif isinstance(iceberg_type, types.ListType):
        element_type = iceberg_to_arrow_type(iceberg_type.element_type)
        return pa.list_(element_type)
    elif isinstance(iceberg_type, types.StructType):
        arrow_fields = []
        for field in iceberg_type.fields:
            arrow_type = iceberg_to_arrow_type(field.field_type)
            arrow_fields.append(pa.field(field.name, arrow_type, nullable=not field.required))
        return pa.struct(arrow_fields)
    elif isinstance(iceberg_type, types.MapType):
        key_type = iceberg_to_arrow_type(iceberg_type.key_type)
        value_type = iceberg_to_arrow_type(iceberg_type.value_type)
        return pa.map_(key_type, value_type)
    else:
        raise ValueError(f"Unsupported Iceberg type: {iceberg_type}")


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


def convert_iceberg_field(field) -> pa.Field:
    """Convert a PyIceberg NestedField to a PyArrow Field."""
    name = field.name
    arrow_type = iceberg_to_arrow_type(field.field_type)
    
    return pa.field(name, arrow_type, nullable=not field.required)


def convert_pyarrow_schema(arrow_schema: pa.Schema) -> IcebergSchema:
    """Convert a PyArrow schema to a PyIceberg schema."""
    fields = [convert_pyarrow_field(i, field) for i, field in enumerate(arrow_schema)]
    return IcebergSchema(*fields)


def convert_iceberg_schema(iceberg_schema: IcebergSchema) -> pa.Schema:
    """Convert a PyIceberg schema to a PyArrow schema."""
    arrow_fields = [convert_iceberg_field(field) for field in iceberg_schema.fields]
    return pa.schema(arrow_fields)


def convert_pyarrow_expression(expr: pc.Expression) -> Optional[BooleanExpression]:
    if expr is None:
        return None

    if expr.op == "and":
        return And(convert_expression(expr.args[0]), convert_expression(expr.args[1]))
    elif expr.op == "or":
        return Or(convert_expression(expr.args[0]), convert_expression(expr.args[1]))
    elif expr.op == "not":
        return Not(convert_expression(expr.args[0]))
    elif expr.op in {"==", "equal"}:
        return EqualTo(Reference(expr.args[0].name), expr.args[1].as_py())
    elif expr.op in {"!=", "not_equal"}:
        return NotEqualTo(Reference(expr.args[0].name), expr.args[1].as_py())
    elif expr.op in {">", "greater"}:
        return GreaterThan(Reference(expr.args[0].name), expr.args[1].as_py())
    elif expr.op == ">=":
        return GreaterThanOrEqual(Reference(expr.args[0].name), expr.args[1].as_py())
    elif expr.op == "<":
        return LessThan(Reference(expr.args[0].name), expr.args[1].as_py())
    elif expr.op == "<=":
        return LessThanOrEqual(Reference(expr.args[0].name), expr.args[1].as_py())
    else:
        raise ValueError(f"Unsupported operation: {expr.op}")


def convert_pyarrow_expressions(exprs: List[pc.Expression]) -> List[BooleanExpression]:
    """
    Convert a list of PyArrow expressions to PyIceberg expressions.
    """
    return [convert_pyarrow_expression(expr) for expr in exprs]
