import pyarrow as pa
import pyiceberg.types as types
from pyiceberg.schema import Schema as IcebergSchema

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
