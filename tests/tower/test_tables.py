import pytest
import shutil
import datetime
import tempfile
import pathlib
from urllib.parse import urljoin
from urllib.request import pathname2url

# We import all the things we need from Tower.
import tower.polars as pl
import tower.pyarrow as pa
from tower.pyiceberg.catalog.memory import InMemoryCatalog

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
    shutil.rmtree(temp_dir)


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
