import pyarrow as pa

from pyiceberg import types as iceberg_types
from pyiceberg.schema import Schema as IcebergSchema


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
