from typing import Optional

import polars as pl
import pyarrow as pa

from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table as IcebergTable

from ._context import TowerContext
from .utils.pyarrow import convert_pyarrow_schema
from .utils.tables import (
    make_table_name,
    namespace_or_default,
)

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

class TableReference:
    def __init__(self, ctx: TowerContext, catalog_name: str, name: str, namespace: Optional[str] = None):
        self._context = ctx
        self._catalog = load_catalog(catalog_name)
        self._name = name
        self._namespace = namespace

    def load(self) -> Table:
        namespace = namespace_or_default(self._namespace)
        table_name = make_table_name(self._name, namespace)
        table = self._catalog.load_table(table_name)
        return Table(self._context, table)

    def create(self, schema: pa.Schema) -> Table:
        namespace = namespace_or_default(self._namespace)
        table_name = make_table_name(self._name, namespace)

        # We need to create the relevant namespace if it's missing from the
        # resolved namespace.
        self._catalog.create_namespace_if_not_exists(namespace)

        # Now that we're certain the namespace exists, we can create the
        # underlying table. This will return an error if something went wrong
        # along the way.
        table = self._catalog.create_table(
            identifier=table_name,
            schema=convert_pyarrow_schema(schema),
        )

        return Table(self._context, table)

    def create_if_not_exists(self, schema: pa.Schema) -> Table:
        namespace = namespace_or_default(self._namespace)
        table_name = make_table_name(self._name, namespace)

        # We need to create the relevant namespace if it's missing from the
        # resolved namespace.
        self._catalog.create_namespace_if_not_exists(namespace)

        # We have the catalog, so let's attempt to create the table. It should
        # not return an error and instead just return the table if it already
        # exists.
        table = self._catalog.create_table_if_not_exists(
            identifier=table_name,
            schema=convert_pyarrow_schema(schema),
        )

        return Table(self._context, table)


def tables(
    name: str,
    catalog: str = "default",
    namespace: Optional[str] = None
) -> TableReference:
    """
    `tables` creates a reference to an Iceberg table with the name `name` from
    the catalog with name `catalog_name`.

    Args:
        `name` (str): The name of the table to load.
        `catalog` (str): The name of the catalog to use. "default" by default.
        `namespace` (Optional[str]): The namespace in which to load the table.

    Returns:
        TableReference: A reference to a table to be resolved with `create` or `load`
    """
    ctx = TowerContext.build()
    return TableReference(ctx, catalog, name, namespace)
