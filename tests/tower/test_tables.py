import pytest
import shutil
import datetime
import tempfile
import pathlib
from urllib.parse import urljoin
from urllib.request import pathname2url

# We import all the things we need from Tower.
import tower.polars as pl
import pyarrow as pa
from pyiceberg.catalog.memory import InMemoryCatalog

# Imports the library under test
import tower


def get_temp_dir():
    """Create a temporary directory and return its file:// URL."""
    # Create a temporary directory that will be automatically cleaned up
    temp_dir = tempfile.TemporaryDirectory()
    abs_path = pathlib.Path(temp_dir.name).absolute()
    file_url = urljoin("file:", pathname2url(str(abs_path)))

    # Return both the URL and the path to the temporary directory
    return file_url, abs_path


@pytest.fixture
def in_memory_catalog():
    file_url, temp_dir = get_temp_dir()
    catalog = InMemoryCatalog("test.in_memory.catalog", warehouse=file_url)

    # Yield the fixture which actually runs the test
    yield catalog

    # Clean up after the catalog
    try:
        shutil.rmtree(temp_dir)
    except FileNotFoundError:
        # Directory was already cleaned up, which is fine
        pass


def test_reading_and_writing_to_tables(in_memory_catalog):
    schema = pa.schema(
        [
            pa.field("id", pa.int64()),
            pa.field("name", pa.string()),
            pa.field("age", pa.int32()),
            pa.field("created_at", pa.timestamp("ms")),
        ]
    )

    ref = tower.tables("users", catalog=in_memory_catalog)
    table = ref.create_if_not_exists(schema)

    data_with_schema = pa.Table.from_pylist(
        [
            {
                "id": 1,
                "name": "Alice",
                "age": 30,
                "created_at": datetime.datetime(2023, 1, 1, 0, 0, 0),
            },
            {
                "id": 2,
                "name": "Bob",
                "age": 25,
                "created_at": datetime.datetime(2023, 1, 2, 0, 0, 0),
            },
            {
                "id": 3,
                "name": "Charlie",
                "age": 35,
                "created_at": datetime.datetime(2023, 1, 3, 0, 0, 0),
            },
        ],
        schema=schema,
    )

    # If we write some data to the table, that should be...OK.
    table = table.insert(data_with_schema)
    assert table is not None
    assert table.rows_affected().inserts == 3

    # Now we should be able to read from the table too.
    df = table.to_polars()

    # Assert that the DF actually can do something useful.
    avg_age = df.select(pl.mean("age").alias("mean_age")).collect().item()
    assert avg_age == 30.0


def test_upsert_to_tables(in_memory_catalog):
    schema = pa.schema(
        [
            pa.field("id", pa.int64()),
            pa.field("username", pa.string()),
            pa.field("name", pa.string()),
            pa.field("age", pa.int32()),
            pa.field("created_at", pa.timestamp("ms")),
        ]
    )

    # First we'll insert some data into the relevant table.
    ref = tower.tables("users", catalog=in_memory_catalog)
    table = ref.create_if_not_exists(schema)

    data_with_schema = pa.Table.from_pylist(
        [
            {
                "id": 1,
                "username": "alicea",
                "name": "Alice",
                "age": 30,
                "created_at": datetime.datetime(2023, 1, 1, 0, 0, 0),
            },
            {
                "id": 2,
                "username": "bobb",
                "name": "Bob",
                "age": 25,
                "created_at": datetime.datetime(2023, 1, 2, 0, 0, 0),
            },
            {
                "id": 3,
                "username": "charliec",
                "name": "Charlie",
                "age": 35,
                "created_at": datetime.datetime(2023, 1, 3, 0, 0, 0),
            },
        ],
        schema=schema,
    )

    # Make sure that we can actually insert the data into the table.
    table = table.insert(data_with_schema)
    assert table is not None
    assert table.rows_affected().inserts == 3

    # Now we'll update records in the table.
    data_with_schema = pa.Table.from_pylist(
        [
            {
                "id": 2,
                "username": "bobb",
                "name": "Bob",
                "age": 26,
                "created_at": datetime.datetime(2023, 1, 2, 0, 0, 0),
            },
        ],
        schema=schema,
    )

    # And make sure we can upsert the data.
    table = table.upsert(data_with_schema, join_cols=["username"])
    assert table.rows_affected().updates == 1

    # Now let's read from the table and see what we get back out.
    df = table.to_polars()
    bob_rows = df.filter(pl.col("username") == "bobb")
    res = bob_rows.select("age").collect()

    # The age should match what we updated the relevant record to
    assert res["age"].item() == 26


def test_delete_from_tables(in_memory_catalog):
    schema = pa.schema(
        [
            pa.field("id", pa.int64()),
            pa.field("username", pa.string()),
            pa.field("name", pa.string()),
            pa.field("age", pa.int32()),
            pa.field("created_at", pa.timestamp("ms")),
        ]
    )

    # First we'll insert some data into the relevant table.
    ref = tower.tables("users", catalog=in_memory_catalog)
    table = ref.create_if_not_exists(schema)

    data_with_schema = pa.Table.from_pylist(
        [
            {
                "id": 1,
                "username": "alicea",
                "name": "Alice",
                "age": 30,
                "created_at": datetime.datetime(2023, 1, 1, 0, 0, 0),
            },
            {
                "id": 2,
                "username": "bobb",
                "name": "Bob",
                "age": 25,
                "created_at": datetime.datetime(2023, 1, 2, 0, 0, 0),
            },
            {
                "id": 3,
                "username": "charliec",
                "name": "Charlie",
                "age": 35,
                "created_at": datetime.datetime(2023, 1, 3, 0, 0, 0),
            },
        ],
        schema=schema,
    )

    # Make sure that we can actually insert the data into the table.
    table = table.insert(data_with_schema)
    assert table is not None
    assert table.rows_affected().inserts == 3

    # Perform the underlying delete from the table...
    table.delete(filters=[table.column("username") == "bobb"])

    # ...and let's make sure that record is actually gone.
    df = table.to_polars()

    # Count all the rows in the table, should be 2.
    all_rows = df.collect()
    assert all_rows.height == 2


def test_getting_schemas_for_tables(in_memory_catalog):
    original_schema = pa.schema(
        [
            pa.field("id", pa.int64()),
            pa.field("username", pa.string()),
            pa.field("name", pa.string()),
            pa.field("age", pa.int32()),
            pa.field("created_at", pa.timestamp("ms")),
        ]
    )

    # First we'll insert some data into the relevant table.
    ref = tower.tables("users", catalog=in_memory_catalog)
    table = ref.create_if_not_exists(original_schema)

    new_schema = table.schema()

    # Should have five columns
    assert len(new_schema) == 5
    assert new_schema.field("id") is not None
    assert new_schema.field("age") is not None
    assert new_schema.field("created_at") is not None


def test_list_of_structs(in_memory_catalog):
    """Tests writing and reading a list of non-nullable structs."""
    table_name = "test_list_of_structs_table"
    # Define a pyarrow schema with a list of structs
    # The list 'tags' can be null, but its elements (structs) are not nullable.
    # Inside the struct, 'key' is non-nullable, 'value' is nullable.
    item_struct_type = pa.struct(
        [
            pa.field("key", pa.string(), nullable=False),  # Non-nullable key
            pa.field("value", pa.int64(), nullable=True),  # Nullable value
        ]
    )
    # The 'item' field represents the elements of the list. It's non-nullable.
    # This means each element in the list must be a valid struct, not a Python None.
    pa_schema = pa.schema(
        [
            pa.field("doc_id", pa.int32(), nullable=False),
            pa.field(
                "tags",
                pa.list_(pa.field("item", item_struct_type, nullable=False)),
                nullable=True,
            ),
        ]
    )

    ref = tower.tables(table_name, catalog=in_memory_catalog)
    table = ref.create_if_not_exists(pa_schema)
    assert table is not None, f"Table '{table_name}' should have been created"

    data_to_write = [
        {
            "doc_id": 1,
            "tags": [{"key": "user", "value": 100}, {"key": "priority", "value": 1}],
        },
        {
            "doc_id": 2,
            "tags": [
                {"key": "source", "value": 200},
                {"key": "reviewed", "value": None},
            ],
        },  # Null value for a struct field
        {"doc_id": 3, "tags": []},  # Empty list
        {"doc_id": 4, "tags": None},  # Null list
    ]
    arrow_table_write = pa.Table.from_pylist(data_to_write, schema=pa_schema)

    op_result = table.insert(arrow_table_write)
    assert op_result is not None
    assert op_result.rows_affected().inserts == 4

    # Read back and verify
    df_read = table.to_polars().collect()  # Collect to get a Polars DataFrame

    assert df_read.shape[0] == 4
    assert df_read["doc_id"].to_list() == [1, 2, 3, 4]

    # Verify nested data (Polars handles structs and lists well)
    # For doc_id = 1
    tags_doc1 = (
        df_read.filter(pl.col("doc_id") == 1).select("tags").row(0)[0]
    )  # Get the list of structs
    assert len(tags_doc1) == 2
    assert tags_doc1[0]["key"] == "user"
    assert tags_doc1[0]["value"] == 100
    assert tags_doc1[1]["key"] == "priority"
    assert tags_doc1[1]["value"] == 1

    # For doc_id = 2 (with a null inside a struct)
    tags_doc2 = df_read.filter(pl.col("doc_id") == 2).select("tags").row(0)[0]
    assert len(tags_doc2) == 2
    assert tags_doc2[0]["key"] == "source"
    assert tags_doc2[0]["value"] == 200
    assert tags_doc2[1]["key"] == "reviewed"
    assert tags_doc2[1]["value"] is None

    # For doc_id = 3 (empty list)
    tags_doc3 = df_read.filter(pl.col("doc_id") == 3).select("tags").row(0)[0]
    assert len(tags_doc3) == 0

    # For doc_id = 4 (null list should also be an empty list)
    tags_doc4 = df_read.filter(pl.col("doc_id") == 4).select("tags").row(0)[0]
    assert tags_doc4 == []


def test_nested_structs(in_memory_catalog):
    """Tests writing and reading a table with nested structs."""
    table_name = "test_nested_structs_table"
    # Define a pyarrow schema with nested structs
    # config: struct<name: string, settings: struct<retries: int8, timeout: int32, active: bool>>
    settings_struct_type = pa.struct(
        [
            pa.field("retries", pa.int8(), nullable=False),
            pa.field("timeout", pa.int32(), nullable=True),
            pa.field("active", pa.bool_(), nullable=False),
        ]
    )
    pa_schema = pa.schema(
        [
            pa.field("record_id", pa.string(), nullable=False),
            pa.field(
                "config",
                pa.struct(
                    [
                        pa.field("name", pa.string(), nullable=True),
                        pa.field(
                            "details", settings_struct_type, nullable=True
                        ),  # This inner struct can be null
                    ]
                ),
                nullable=True,
            ),  # The outer 'config' struct can also be null
        ]
    )

    ref = tower.tables(table_name, catalog=in_memory_catalog)
    table = ref.create_if_not_exists(pa_schema)
    assert table is not None, f"Table '{table_name}' should have been created"

    data_to_write = [
        {
            "record_id": "rec1",
            "config": {
                "name": "Default",
                "details": {"retries": 3, "timeout": 1000, "active": True},
            },
        },
        {
            "record_id": "rec2",
            "config": {
                "name": "Fast",
                "details": {"retries": 1, "timeout": None, "active": True},
            },
        },  # Null timeout
        {
            "record_id": "rec3",
            "config": {"name": "Inactive", "details": None},
        },  # Null inner struct
        {"record_id": "rec4", "config": None},  # Null outer struct
    ]
    arrow_table_write = pa.Table.from_pylist(data_to_write, schema=pa_schema)

    op_result = table.insert(arrow_table_write)
    assert op_result is not None
    assert op_result.rows_affected().inserts == 4

    # Read back and verify
    df_read = table.to_polars().collect()

    assert df_read.shape[0] == 4
    assert df_read["record_id"].to_list() == ["rec1", "rec2", "rec3", "rec4"]

    # Verify nested data for rec1
    config_rec1 = (
        df_read.filter(pl.col("record_id") == "rec1").select("config").row(0)[0]
    )
    assert config_rec1["name"] == "Default"
    details_rec1 = config_rec1["details"]
    assert details_rec1["retries"] == 3
    assert details_rec1["timeout"] == 1000
    assert details_rec1["active"] is True

    # Verify nested data for rec2 (null timeout)
    config_rec2 = (
        df_read.filter(pl.col("record_id") == "rec2").select("config").row(0)[0]
    )
    assert config_rec2["name"] == "Fast"
    details_rec2 = config_rec2["details"]
    assert details_rec2["retries"] == 1
    assert details_rec2["timeout"] is None
    assert details_rec2["active"] is True

    # Verify nested data for rec3 (null inner struct 'details')
    config_rec3 = (
        df_read.filter(pl.col("record_id") == "rec3").select("config").row(0)[0]
    )
    assert config_rec3["name"] == "Inactive"
    assert config_rec3["details"] is None  # The 'details' struct itself is null

    # Verify nested data for rec4 (null outer struct 'config')
    config_rec4 = (
        df_read.filter(pl.col("record_id") == "rec4").select("config").row(0)[0]
    )
    assert config_rec4 is None  # The 'config' struct is null


def test_list_of_primitive_types(in_memory_catalog):
    """Tests writing and reading a list of primitive types."""
    table_name = "test_list_of_primitives_table"
    pa_schema = pa.schema(
        [
            pa.field("event_id", pa.int32(), nullable=False),
            pa.field(
                "scores",
                pa.list_(pa.field("score", pa.float32(), nullable=False)),
                nullable=True,
            ),  # List of non-nullable floats
            pa.field(
                "keywords",
                pa.list_(pa.field("keyword", pa.string(), nullable=True)),
                nullable=True,
            ),  # List of nullable strings
        ]
    )

    ref = tower.tables(table_name, catalog=in_memory_catalog)
    table = ref.create_if_not_exists(pa_schema)
    assert table is not None, f"Table '{table_name}' should have been created"

    data_to_write = [
        {"event_id": 1, "scores": [1.0, 2.5, 3.0], "keywords": ["alpha", "beta", None]},
        {"event_id": 2, "scores": [], "keywords": ["gamma"]},
        {"event_id": 3, "scores": None, "keywords": None},
        {"event_id": 4, "scores": [4.2], "keywords": []},
    ]
    arrow_table_write = pa.Table.from_pylist(data_to_write, schema=pa_schema)

    op_result = table.insert(arrow_table_write)
    assert op_result is not None
    assert op_result.rows_affected().inserts == 4

    df_read = table.to_polars().collect()

    assert df_read.shape[0] == 4

    # Event 1
    row1 = df_read.filter(pl.col("event_id") == 1)
    assert row1.select("scores").to_series()[0].to_list() == [1.0, 2.5, 3.0]
    assert row1.select("keywords").to_series()[0].to_list() == ["alpha", "beta", None]

    # Event 2
    row2 = df_read.filter(pl.col("event_id") == 2)
    assert row2.select("scores").to_series()[0].to_list() == []
    assert row2.select("keywords").to_series()[0].to_list() == ["gamma"]

    # Event 3
    row3 = df_read.filter(pl.col("event_id") == 3)
    assert row3.select("scores").to_series()[0] is None
    assert row3.select("keywords").to_series()[0] is None


def test_map_type_simple(in_memory_catalog):
    """Tests writing and reading a simple map type."""
    table_name = "test_map_type_simple_table"
    # Map from string to string. Keys are non-nullable, values can be nullable.
    pa_schema = pa.schema(
        [
            pa.field("id", pa.int32(), nullable=False),
            pa.field(
                "properties",
                pa.map_(pa.string(), pa.string(), keys_sorted=False),
                nullable=True,
            ),
            # Note: PyArrow map values are nullable by default if item_field is not specified with nullable=False
        ]
    )

    ref = tower.tables(table_name, catalog=in_memory_catalog)
    table = ref.create_if_not_exists(pa_schema)
    assert table is not None, f"Table '{table_name}' should have been created"

    # PyArrow represents maps as a list of structs with 'key' and 'value' fields
    data_to_write = [
        {"id": 1, "properties": [("color", "blue"), ("size", "large")]},
        {
            "id": 2,
            "properties": [("status", "pending"), ("owner", None)],
        },  # Null value in map
        {"id": 3, "properties": []},  # Empty map
        {"id": 4, "properties": None},  # Null map field
    ]
    arrow_table_write = pa.Table.from_pylist(data_to_write, schema=pa_schema)

    op_result = table.insert(arrow_table_write)
    assert op_result is not None
    assert op_result.rows_affected().inserts == 4

    df_read = table.to_polars().collect()
    assert df_read.shape[0] == 4

    # Verify map data
    # Polars represents map as list of structs: struct<fields=[Field(key:Utf8), Field(value:Utf8)]>
    # Row 1
    props1_series = df_read.filter(pl.col("id") == 1).select("properties").to_series()
    # The series item is already a list of dictionaries
    props1_list = props1_series[0]
    expected_props1 = [
        {"key": "color", "value": "blue"},
        {"key": "size", "value": "large"},
    ]
    # Sort by key for consistent comparison if order is not guaranteed
    assert sorted(props1_list, key=lambda x: x["key"]) == sorted(
        expected_props1, key=lambda x: x["key"]
    )

    # Row 2
    props2_series = df_read.filter(pl.col("id") == 2).select("properties").to_series()
    props2_list = props2_series[0]
    expected_props2 = [
        {"key": "status", "value": "pending"},
        {"key": "owner", "value": None},
    ]
    assert sorted(props2_list, key=lambda x: x["key"]) == sorted(
        expected_props2, key=lambda x: x["key"]
    )

    # Row 3 (empty map)
    props3_series = df_read.filter(pl.col("id") == 3).select("properties").to_series()
    assert props3_series[0].to_list() == []

    # Row 4 (null map)
    props4_series = df_read.filter(pl.col("id") == 4).select("properties").to_series()
    assert props4_series[0] is None


def test_drop_existing_table(in_memory_catalog):
    """Test dropping an existing table returns True."""
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("name", pa.string()),
    ])

    # Create a table first
    ref = tower.tables("users_to_drop", catalog=in_memory_catalog)
    table = ref.create(schema)
    assert table is not None

    # Insert some data to make sure the table exists and has content
    data = pa.Table.from_pylist([{"id": 1, "name": "Alice"}], schema=schema)
    table.insert(data)

    # Verify the table exists by reading from it
    df = table.read()
    assert len(df) == 1

    # Now drop the table - should return True
    success = ref.drop()
    assert success is True


def test_drop_nonexistent_table(in_memory_catalog):
    """Test dropping a non-existent table returns False."""
    ref = tower.tables("nonexistent_table", catalog=in_memory_catalog)

    # Try to drop a table that doesn't exist - should return False
    success = ref.drop()
    assert success is False


def test_drop_table_with_namespace(in_memory_catalog):
    """Test dropping a table with a specific namespace."""
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("data", pa.string()),
    ])

    # Create a table in a specific namespace
    ref = tower.tables("test_table", catalog=in_memory_catalog, namespace="test_namespace")
    table = ref.create(schema)
    assert table is not None

    # Insert some data to confirm the table exists
    data = pa.Table.from_pylist([{"id": 1, "data": "test"}], schema=schema)
    table.insert(data)

    # Verify we can read from it
    df = table.read()
    assert len(df) == 1

    # Drop the table - should succeed
    success = ref.drop()
    assert success is True

    # Try to drop the same table again - should return False
    success_again = ref.drop()
    assert success_again is False


def test_drop_and_recreate_table(in_memory_catalog):
    """Test that we can drop a table and then recreate it."""
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("value", pa.string()),
    ])

    table_name = "drop_recreate_test"
    ref = tower.tables(table_name, catalog=in_memory_catalog)

    # Create and populate the table
    table = ref.create(schema)
    data = pa.Table.from_pylist([
        {"id": 1, "value": "first"},
        {"id": 2, "value": "second"}
    ], schema=schema)
    table.insert(data)

    # Verify original data
    df = table.read()
    assert len(df) == 2

    # Drop the table
    success = ref.drop()
    assert success is True

    # Recreate the table with different data
    new_table = ref.create(schema)
    new_data = pa.Table.from_pylist([
        {"id": 10, "value": "new_first"},
        {"id": 20, "value": "new_second"},
        {"id": 30, "value": "new_third"}
    ], schema=schema)
    new_table.insert(new_data)

    # Verify new data
    new_df = new_table.read()
    assert len(new_df) == 3

    # Make sure the old data is gone
    ids = new_df.select("id").to_series().to_list()
    assert 1 not in ids
    assert 2 not in ids
    assert 10 in ids
    assert 20 in ids
    assert 30 in ids


def test_drop_multiple_tables(in_memory_catalog):
    """Test dropping multiple tables."""
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("name", pa.string()),
    ])

    # Create multiple tables
    table_names = ["table1", "table2", "table3"]
    tables = {}

    for name in table_names:
        ref = tower.tables(name, catalog=in_memory_catalog)
        table = ref.create(schema)
        data = pa.Table.from_pylist([{"id": 1, "name": f"data_{name}"}], schema=schema)
        table.insert(data)
        tables[name] = ref

    # Verify all tables exist by reading from them
    for name, ref in tables.items():
        table = ref.load()
        df = table.read()
        assert len(df) == 1

    # Drop all tables
    for name, ref in tables.items():
        success = ref.drop()
        assert success is True, f"Failed to drop table {name}"

    # Verify all tables are gone
    for name, ref in tables.items():
        success = ref.drop()
        assert success is False, f"Table {name} still exists after dropping"
