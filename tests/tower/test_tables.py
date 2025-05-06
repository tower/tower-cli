import pytest
import shutil
import datetime

import polars as pl
import pyarrow as pa
from pyiceberg.catalog.memory import InMemoryCatalog

@pytest.fixture
def in_memory_catalog():
    catalog = InMemoryCatalog("test.in_memory.catalog", warehouse="file:///tmp/iceberg")

    # Yield the fixture which actually runs the test
    yield catalog

    # Clean up after the catalog
    shutil.rmtree("/tmp/iceberg")


def test_reading_and_writing_to_tables(in_memory_catalog):
    schema = pa.schema([
        pa.field("id", pa.int64()),
        pa.field("name", pa.string()),
        pa.field("age", pa.int32()),
        pa.field("created_at", pa.timestamp("ms")),
    ]) 

    import tower
    ref = tower.tables("some_table", catalog=in_memory_catalog)
    table = ref.create_if_not_exists(schema)

    data_with_schema = pa.Table.from_pylist([
        {"id": 1, "name": "Alice", "age": 30, "created_at": datetime.datetime(2023, 1, 1, 0, 0, 0)},
        {"id": 2, "name": "Bob", "age": 25, "created_at": datetime.datetime(2023, 1, 2, 0, 0, 0)},
        {"id": 3, "name": "Charlie", "age": 35, "created_at": datetime.datetime(2023, 1, 3, 0, 0, 0)},
    ], schema=schema)

    # If we write some data to the table, that should be...OK.
    table = table.insert(data_with_schema)
    assert table is not None
    assert table.rows_affected().inserts == 3

    # Now we should be able to read from the table too.
    df = table.to_polars()

    # Assert that the DF actually can do something useful.
    avg_age = df.select(pl.mean("age").alias("mean_age")).collect().item()
    assert avg_age == 30.0
