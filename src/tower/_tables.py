from typing import Optional, Generic, TypeVar, Union, List
from dataclasses import dataclass

TTable = TypeVar("TTable", bound="Table")

import polars as pl
import pyarrow as pa
import pyarrow.compute as pc

from pyiceberg.table import Table as IcebergTable
from pyiceberg.catalog import (
    Catalog,
    load_catalog,
)

from ._context import TowerContext
from .utils.pyarrow import (
    convert_pyarrow_schema,
    convert_pyarrow_expressions,
)
from .utils.tables import (
    make_table_name,
    namespace_or_default,
)

@dataclass
class RowsAffectedInformation:
    inserts: int
    updates: int


class Table:
    """
    `Table` is a wrapper around an Iceberg table. It provides methods to read and
    write data to the table.
    """

    def __init__(self, context: TowerContext, table: IcebergTable):
        self._stats = RowsAffectedInformation(0, 0)
        self._context = context
        self._table = table


    def read(self) -> pl.DataFrame:
        """
        Reads from the Iceberg tables. Returns the results as a Polars DataFrame.
        """
        # We call `collect` here to force the execution of the query and get
        # the result as a DataFrame.
        return pl.scan_iceberg(self._table).collect()


    def to_polars(self) -> pl.LazyFrame:
        """
        Converts the table to a Polars LazyFrame. This is useful when you
        understand Polars and you want to do something more complicated.
        """
        return pl.scan_iceberg(self._table)


    def rows_affected(self) -> RowsAffectedInformation:
        """
        Returns the stats for the table. This includes the number of inserts,
        updates, and deletes.
        """
        return self._stats


    def insert(self, data: pa.Table) -> TTable:
        """
        Inserts data into the Iceberg table. The data is expressed as a PyArrow table.

        Args:
            data (pa.Table): The data to insert into the table.

        Returns:
            TTable: The table with the inserted rows.
        """
        self._table.append(data)
        self._stats.inserts += data.num_rows
        return self


    def upsert(self, data: pa.Table, join_cols: Optional[list[str]] = None) -> TTable:
        """
        Upserts data into the Iceberg table. The data is expressed as a PyArrow table.

        Args:
            data (pa.Table): The data to upsert into the table.
            join_cols (Optional[list[str]]): The columns that form the key to match rows on

        Returns:
            TTable: The table with the upserted rows.
        """
        res = self._table.upsert(
            data,
            join_cols=join_cols,

            # All upserts will always be case sensitive. Perhaps we'll add this
            # as a parameter in the future?
            case_sensitive=True,
            
            # These are the defaults, but we're including them to be complete.
            when_matched_update_all=True,
            when_not_matched_insert_all=True,
        )

        # Update the stats with the results of the relevant upsert.
        self._stats.updates += res.rows_updated
        self._stats.inserts += res.rows_inserted

        return self


    def delete(self, filters: Union[str, List[pc.Expression]]) -> TTable:
        """
        Deletes data from the Iceberg table. The filters are expressed as a
        PyArrow expression. The filters are applied to the table and the
        matching rows are deleted.

        Args:
            filters (Union[str, List[pc.Expression]]): The filters to apply to the table.
                This can be a string or a list of PyArrow expressions.

        Returns:
            TTable: The table with the deleted rows.
        """
        if isinstance(filters, list):
            # We need to convert the pc.Expression into PyIceberg
            next_filters = convert_pyarrow_expressions(filters)
            filters = next_filters

        self._table.delete(
            delete_filter=filters,

            # We want this to always be the case. Not sure why you wouldn't?
            case_sensitive=True,
        )

        # NOTE: There is, unfortunately, no way to get the number of rows
        # deleted besides comparing the two snapshots that were created.

        return self


    def schema(self) -> pa.Schema:
        # We take an Iceberg Schema and we need to convert it into a PyArrow Schema
        iceberg_schema = self._table.schema()
        return iceberg_schema.as_arrow()


    def column(self, name: str) -> pa.compute.Expression:
        """
        Returns a column from the table. This is useful when you want to
        perform some operations on the column.
        """
        field = self.schema().field(name)
        
        if field is None:
            raise ValueError(f"Column {name} not found in table schema")

        # We need to convert the PyArrow field into pa.compute.Expression
        return pa.compute.field(name)


class TableReference:
    def __init__(self, ctx: TowerContext, catalog: Catalog, name: str, namespace: Optional[str] = None):
        self._context = ctx
        self._catalog = catalog
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
    catalog: Union[str, Catalog] = "default",
    namespace: Optional[str] = None
) -> TableReference:
    """
    `tables` creates a reference to an Iceberg table with the name `name` from
    the catalog with name `catalog_name`.

    Args:
        `name` (str): The name of the table to load.
        `catalog` (Union[str, Catalog]): The name of the catalog or the actual
            catalog to use. "default" is the default value. You can pass in an
            actual catalog object for testing purposes.
        `namespace` (Optional[str]): The namespace in which to load the table.

    Returns:
        TableReference: A reference to a table to be resolved with `create` or `load`
    """
    if isinstance(catalog, str):
        catalog = load_catalog(catalog)

    ctx = TowerContext.build()
    return TableReference(ctx, catalog, name, namespace)
