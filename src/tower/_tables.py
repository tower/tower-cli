from typing import Optional

from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table as IcebergTable
from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.types import (
    BooleanType, IntegerType, LongType, FloatType, DoubleType, StringType,
    DateType, TimestampType, BinaryType, DecimalType, ListType, MapType, StructType,
    NestedField
)

from .utils.pyarrow import convert_pyarrow_schema
from .utils.tables import (
    make_table_name,
    namespace_or_default,
)

import polars as pl
import pyarrow as pa

from ._context import TowerContext

class Table:
    """
    `Table` is a wrapper around an Iceberg table. It provides methods to read and
    write data to the table.
    """

    def __init__(self, context: TowerContext, table: IcebergTable):
        self._context = context
        self._table = table

    def read(self) -> pl.DataFrame:
        """
        Reads from the Iceberg tables. Returns the results as a Polars DataFrame.
        """
        # We call `collect` here to force the execution of the query and get
        # the result as a DataFrame.
        return pl.scan_iceberg(self._table).collect()

    def insert(self, data: pa.Table):
        """
        Inserts data into the Iceberg table. The data is expressed as a PyArrow table.

        Args:
            data (pa.Table): The data to insert into the table.
        """
        self._table.append(data)

def create_table(
    catalog_name: str,
    name: str,
    schema: pa.Schema,
    namespace: Optional[str] = None
) -> Table:
    """
    `create_table` creates a new Iceberg table with the name `name` and the
    supplied schema in the catalog `catalog_name`. The schema is expressed as a
    PyArrow schema.

    Args:
        catalog_name (str): The name of the catalog to use.
        name (str): The name of the table to create.
        schema (pa.Schema): The schema of the table to create.
        namespace (Optional[str]): The namespace in which to create the table.

    Returns:
        Table: The created table
    """
    ctx = TowerContext.build()
    catalog = load_catalog(catalog_name)
    namespace = namespace_or_default(namespace)

    # We need to create the relevant namespace if it's missing from the
    # resolved namespace.
    catalog.create_namespace_if_not_exists(namespace)

    # Now that we 
    table = catalog.create_table(
        identifier=make_table_name(name, namespace),
        schema=convert_pyarrow_schema(schema),
    )
    return Table(ctx, table)


def load_table(
    catalog_name: str,
    name: str,
    namespace: Optional[str] = None
) -> Table:
    """
    `load_table` loads an Iceberg table with the name `name` from the catalog
    with name `catalog_name`.

    Args:
        `catalog_name` (str): The name of the catalog to use.
        `name` (str): The name of the table to load.
        `namespace` (Optional[str]): The namespace in which to load the table.

    Returns:
        Table: The table
    """
    ctx = TowerContext.build()
    namespace = namespace_or_default(namespace)
    catalog = load_catalog(catalog_name)
    table = catalog.load_table(make_table_name(name, namespace))

    return Table(ctx, table)
