from typing import Optional, Generic, TypeVar, Union, List
from dataclasses import dataclass

from pyiceberg.exceptions import NoSuchTableError

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
        """
        Initialize a new Table instance that wraps an Iceberg table.

        This constructor creates a Table object that provides a high-level interface
        for interacting with an Iceberg table. It initializes the table statistics
        tracking and stores the necessary context and table references.

        Args:
            context (TowerContext): The context in which the table operates, providing
                configuration and environment settings.
            table (IcebergTable): The underlying Iceberg table instance to be wrapped.

        Attributes:
            _stats (RowsAffectedInformation): Tracks the number of rows affected by
                insert and update operations. Initialized with zero counts.
            _context (TowerContext): The context in which the table operates.
            _table (IcebergTable): The underlying Iceberg table instance.

        Example:
            >>> # Create a table reference and load it
            >>> table_ref = tables("my_table")
            >>> table = table_ref.load()  # This internally calls Table.__init__
        """

        self._stats = RowsAffectedInformation(0, 0)
        self._context = context
        self._table = table

    def read(self) -> pl.DataFrame:
        """
        Reads all data from the Iceberg table and returns it as a Polars DataFrame.

        This method executes a full table scan and materializes the results into memory
        as a Polars DataFrame. For large tables, consider using `to_polars()` to get a
        LazyFrame that can be processed incrementally.

        Returns:
            pl.DataFrame: A Polars DataFrame containing all rows from the table.

        Example:
            >>> table = tables("my_table").load()
            >>> # Read all data into a DataFrame
            >>> df = table.read()
            >>> # Perform operations on the DataFrame
            >>> filtered_df = df.filter(pl.col("age") > 30)
            >>> # Get basic statistics
            >>> print(df.describe())
        """
        # We call `collect` here to force the execution of the query and get
        # the result as a DataFrame.
        return pl.scan_iceberg(self._table).collect()

    def to_polars(self) -> pl.LazyFrame:
        """
        Converts the table to a Polars LazyFrame for efficient, lazy evaluation.

        This method returns a LazyFrame that allows for building complex query plans
        without immediately executing them. This is particularly useful for:
        - Processing large tables that don't fit in memory
        - Building complex transformations and aggregations
        - Optimizing query performance through Polars' query optimizer

        Returns:
            pl.LazyFrame: A Polars LazyFrame representing the table data.

        Example:
            >>> table = tables("my_table").load()
            >>> # Create a lazy query plan
            >>> lazy_df = table.to_polars()
            >>> # Build complex transformations
            >>> result = (lazy_df
            ...     .filter(pl.col("age") > 30)
            ...     .groupby("department")
            ...     .agg(pl.col("salary").mean())
            ...     .sort("department"))
            >>> # Execute the plan
            >>> final_df = result.collect()
        """
        return pl.scan_iceberg(self._table)

    def rows_affected(self) -> RowsAffectedInformation:
        """
        Returns statistics about the number of rows affected by write operations on the table.

        This method tracks the cumulative number of rows that have been inserted or updated
        through operations like `insert()` and `upsert()`. Note that delete operations are
        not currently tracked due to limitations in the underlying Iceberg implementation.

        Returns:
            RowsAffectedInformation: An object containing:
                - inserts (int): Total number of rows inserted
                - updates (int): Total number of rows updated

        Example:
            >>> table = tables("my_table").load()
            >>> # Insert some data
            >>> table.insert(new_data)
            >>> # Upsert some data
            >>> table.upsert(updated_data, join_cols=["id"])
            >>> # Check the impact of our operations
            >>> stats = table.rows_affected()
            >>> print(f"Inserted {stats.inserts} rows")
            >>> print(f"Updated {stats.updates} rows")
        """
        return self._stats

    def insert(self, data: pa.Table) -> TTable:
        """
        Inserts new rows into the Iceberg table.

        This method appends the provided data to the table. The data must be provided as a
        PyArrow table with a schema that matches the table's schema. The operation is
        tracked in the table's statistics, incrementing the insert count.

        Args:
            data (pa.Table): The data to insert into the table. The schema of this table
                must match the schema of the target table.

        Returns:
            TTable: The table instance with the newly inserted rows, allowing for method chaining.

        Example:
            >>> table = tables("my_table").load()
            >>> # Create a PyArrow table with new data
            >>> new_data = pa.table({
            ...     "id": [1, 2, 3],
            ...     "name": ["Alice", "Bob", "Charlie"],
            ...     "age": [25, 30, 35]
            ... })
            >>> # Insert the data
            >>> table.insert(new_data)
            >>> # Verify the insertion
            >>> stats = table.rows_affected()
            >>> print(f"Inserted {stats.inserts} rows")
        """
        self._table.append(data)
        self._stats.inserts += data.num_rows
        return self

    def upsert(self, data: pa.Table, join_cols: Optional[list[str]] = None) -> TTable:
        """
        Performs an upsert operation (update or insert) on the Iceberg table.

        This method will:
        - Update existing rows if they match the join columns
        - Insert new rows if no match is found
        All operations are case-sensitive by default.

        Args:
            data (pa.Table): The data to upsert into the table. The schema of this table
                must match the schema of the target table.
            join_cols (Optional[list[str]]): The columns that form the key to match rows on.
                If not provided, all columns will be used for matching.

        Returns:
            TTable: The table instance with the upserted rows, allowing for method chaining.

        Note:
            - The operation is always case-sensitive
            - When a match is found, all columns are updated
            - When no match is found, the row is inserted
            - The operation is tracked in the table's statistics

        Example:
            >>> table = tables("my_table").load()
            >>> # Create a PyArrow table with data to upsert
            >>> data = pa.table({
            ...     "id": [1, 2, 3],
            ...     "name": ["Alice", "Bob", "Charlie"],
            ...     "age": [26, 31, 36]  # Updated ages
            ... })
            >>> # Upsert the data using 'id' as the key
            >>> table.upsert(data, join_cols=["id"])
            >>> # Verify the operation
            >>> stats = table.rows_affected()
            >>> print(f"Updated {stats.updates} rows")
            >>> print(f"Inserted {stats.inserts} rows")
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
        Deletes rows from the Iceberg table that match the specified filter conditions.

        This method removes rows from the table based on the provided filter expressions.
        The operation is always case-sensitive. Note that the number of deleted rows
        cannot be tracked due to limitations in the underlying Iceberg implementation.

        Args:
            filters (Union[str, List[pc.Expression]]): The filter conditions to apply.
                Can be either:
                - A single PyArrow compute expression
                - A list of PyArrow compute expressions (combined with AND)
                - A string expression

        Returns:
            TTable: The table instance with the deleted rows, allowing for method chaining.

        Note:
            - The operation is always case-sensitive
            - The number of deleted rows cannot be tracked in the table statistics
            - To get the number of deleted rows, you would need to compare snapshots

        Example:
            >>> table = tables("my_table").load()
            >>> # Delete rows where age is greater than 30
            >>> table.delete(table.column("age") > 30)
            >>> # Delete rows matching multiple conditions
            >>> table.delete([
            ...     table.column("age") > 30,
            ...     table.column("department") == "IT"
            ... ])
            >>> # Delete rows using a string expression
            >>> table.delete("age > 30 AND department = 'IT'")
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
        """
        Returns the schema of the table as a PyArrow schema.

        This method converts the underlying Iceberg table schema into a PyArrow schema,
        which can be used for type information and schema validation.

        Returns:
            pa.Schema: The PyArrow schema representation of the table's structure.
        Example:
            >>> table = tables("my_table").load()
            >>> schema = table.schema()
        """
        iceberg_schema = self._table.schema()
        return iceberg_schema.as_arrow()

    def column(self, name: str) -> pa.compute.Expression:
        """
        Returns a column from the table as a PyArrow compute expression.

        This method is useful for creating column-based expressions that can be used in
        operations like filtering, sorting, or aggregating data. The returned expression
        can be used with PyArrow's compute functions.

        Args:
            name (str): The name of the column to retrieve from the table schema.

        Returns:
            pa.compute.Expression: A PyArrow compute expression representing the column.

        Raises:
            ValueError: If the specified column name is not found in the table schema.

        Example:
            >>> table = tables("my_table").load()
            >>> # Create a filter expression for rows where age > 30
            >>> age_expr = table.column("age") > 30
            >>> # Use the expression in a delete operation
            >>> table.delete(age_expr)
        """
        field = self.schema().field(name)

        if field is None:
            raise ValueError(f"Column {name} not found in table schema")

        # We need to convert the PyArrow field into pa.compute.Expression
        return pa.compute.field(name)


class TableReference:
    def __init__(
        self,
        ctx: TowerContext,
        catalog: Catalog,
        name: str,
        namespace: Optional[str] = None,
    ):
        self._context = ctx
        self._catalog = catalog
        self._name = name
        self._namespace = namespace

    def load(self) -> Table:
        """
        Loads an existing Iceberg table from the catalog.

        This method resolves the table's namespace and name, then loads the table
        from the catalog. If the table doesn't exist, this will raise an error.
        Use `create()` or `create_if_not_exists()` to create new tables.

        Returns:
            Table: A new Table instance wrapping the loaded Iceberg table.

        Raises:
            TableNotFoundError: If the table doesn't exist in the catalog.

        Example:
            >>> # Load the existing table
            >>> table = tables("my_table", namespace="my_namespace").load()
            >>> # Now you can use the table
            >>> df = table.read()
        """

        namespace = namespace_or_default(self._namespace)
        table_name = make_table_name(self._name, namespace)
        table = self._catalog.load_table(table_name)
        return Table(self._context, table)

    def create(self, schema: pa.Schema) -> Table:
        """
        Creates a new Iceberg table with the specified schema.

        This method will:
        1. Resolve the table's namespace (using default if not specified)
        2. Create the namespace if it doesn't exist
        3. Create a new table with the provided schema
        4. Return a Table instance for the newly created table

        Args:
            schema (pa.Schema): The PyArrow schema defining the structure of the table.
                This will be converted to an Iceberg schema internally.

        Returns:
            Table: A new Table instance wrapping the created Iceberg table.

        Raises:
            TableAlreadyExistsError: If a table with the same name already exists in the namespace.
            NamespaceError: If there are issues creating or accessing the namespace.

        Example:
            >>> # Define the table schema
            >>> schema = pa.schema([
            ...     pa.field("id", pa.int64()),
            ...     pa.field("name", pa.string()),
            ...     pa.field("age", pa.int32())
            ... ])
            >>> # Create the table
            >>> table = tables("my_table", namespace="my_namespace").create(schema)
            >>> # Now you can use the table
            >>> table.insert(new_data)
        """

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
        """
        Creates a new Iceberg table if it doesn't exist, or returns the existing table.

        This method will:
        1. Resolve the table's namespace (using default if not specified)
        2. Create the namespace if it doesn't exist
        3. Create a new table with the provided schema if it doesn't exist
        4. Return the existing table if it already exists
        5. Return a Table instance for the table

        Unlike `create()`, this method will not raise an error if the table already exists.
        Instead, it will return the existing table, making it safe for idempotent operations.

        Args:
            schema (pa.Schema): The PyArrow schema defining the structure of the table.
                This will be converted to an Iceberg schema internally. Note that this
                schema is only used if the table needs to be created.

        Returns:
            Table: A Table instance wrapping either the newly created or existing Iceberg table.

        Raises:
            NamespaceError: If there are issues creating or accessing the namespace.

        Example:
            >>> # Define the table schema
            >>> schema = pa.schema([
            ...     pa.field("id", pa.int64()),
            ...     pa.field("name", pa.string()),
            ...     pa.field("age", pa.int32())
            ... ])
            >>> # Create the table if it doesn't exist
            >>> table = tables("my_table", namespace="my_namespace").create_if_not_exists(schema)
            >>> # This is safe to call multiple times
            >>> table = tables("my_table", namespace="my_namespace").create_if_not_exists(schema)
        """

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

    def drop(self) -> bool:
        """
        Drops (deletes) the Iceberg table from the catalog.

        This method will:
        1. Resolve the table's namespace (using default if not specified)
        2. Drop the table from the catalog
        3. Return True if successful, False if the table didn't exist

        Returns:
            bool: True if the table was successfully dropped, False if it didn't exist.

        Raises:
            CatalogError: If there are issues accessing the catalog or dropping the table.

        Example:
            >>> # Drop an existing table
            >>> table_ref = tables("my_table", namespace="my_namespace")
            >>> success = table_ref.drop()
            >>> if success:
            ...     print("Table dropped successfully")
            ... else:
            ...     print("Table didn't exist")
        """
        namespace = namespace_or_default(self._namespace)
        table_name = make_table_name(self._name, namespace)

        try:
            self._catalog.drop_table(table_name)
            return True
        except NoSuchTableError:
            # If the table doesn't exist or there's any other issue, return False
            # The underlying PyIceberg catalog will raise different exceptions
            # depending on the catalog implementation, so we catch all exceptions
            return False


def tables(
    name: str, catalog: Union[str, Catalog] = "default", namespace: Optional[str] = None
) -> TableReference:
    """
    Creates a reference to an Iceberg table that can be used to load or create tables.

    This function is the main entry point for working with Iceberg tables in Tower. It returns
    a TableReference object that can be used to either load an existing table or create a new one.
    The actual table operations (read, write, etc.) are performed through the Table instance
    obtained by calling `load()` or `create()` on the returned reference.

    Args:
        name (str): The name of the table to reference. This will be used to either load
            an existing table or create a new one.
        catalog (Union[str, Catalog], optional): The catalog to use. Can be either:
            - A string name of the catalog (defaults to "default")
            - A Catalog instance (useful for testing or custom catalog implementations)
            Defaults to "default".
        namespace (Optional[str], optional): The namespace in which the table exists or
            should be created. If not provided, a default namespace will be used.

    Returns:
        TableReference: A reference object that can be used to:
            - Load an existing table using `load()`
            - Create a new table using `create()`
            - Create a table if it doesn't exist using `create_if_not_exists()`
            - Drop an existing table using `drop()`

    Raises:
        CatalogError: If there are issues accessing or loading the specified catalog.
        TableNotFoundError: When trying to load a non-existent table (only if `load()` is called).

    Examples:
        >>> # Load an existing table from the default catalog
        >>> table = tables("my_table").load()
        >>> df = table.read()

        >>> # Create a new table in a specific namespace
        >>> schema = pa.schema([
        ...     pa.field("id", pa.int64()),
        ...     pa.field("name", pa.string())
        ... ])
        >>> table = tables("new_table", namespace="my_namespace").create(schema)

        >>> # Use a specific catalog
        >>> table = tables("my_table", catalog="my_catalog").load()

        >>> # Create a table if it doesn't exist
        >>> table = tables("my_table").create_if_not_exists(schema)

        >>> # Drop an existing table
        >>> success = tables("my_table", namespace="my_namespace").drop()
        >>> if success:
        ...     print("Table dropped successfully")
    """
    if isinstance(catalog, str):
        catalog = load_catalog(catalog)

    ctx = TowerContext.build()
    return TableReference(ctx, catalog, name, namespace)
