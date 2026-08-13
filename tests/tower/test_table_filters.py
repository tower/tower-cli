import operator

import pyarrow.compute as pc
import pytest
from pyiceberg.expressions import (
    And,
    EqualTo,
    GreaterThan,
    GreaterThanOrEqual,
    LessThan,
    LessThanOrEqual,
    NotEqualTo,
    Or,
)
from pyiceberg.schema import Schema
from pyiceberg.types import IntegerType, NestedField, StringType, StructType

import tower._tables as tables_module
from tower._context import TowerContext
from tower.exceptions import PyArrowFilterMigrationError


class FakeFilterTable:
    def __init__(self):
        self.delete_calls = []
        self._schema = Schema(
            NestedField(1, "age", IntegerType(), required=False),
            NestedField(2, "brand", StringType(), required=False),
            NestedField(3, "origin", StringType(), required=False),
            NestedField(4, "notice", StringType(), required=False),
            NestedField(
                5,
                "profile",
                StructType(
                    NestedField(6, "name", StringType(), required=False),
                ),
                required=False,
            ),
        )

    def schema(self):
        return self._schema

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)

    def refresh(self):
        raise AssertionError("a successful delete must not refresh")


def make_table():
    context = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
    )
    iceberg_table = FakeFilterTable()
    return tables_module.Table(context, iceberg_table), iceberg_table


@pytest.mark.parametrize(
    ("comparison", "expected"),
    [
        (lambda column: operator.eq(column, 18), EqualTo("age", 18)),
        (lambda column: operator.ne(column, 18), NotEqualTo("age", 18)),
        (lambda column: operator.gt(column, 18), GreaterThan("age", 18)),
        (lambda column: operator.ge(column, 18), GreaterThanOrEqual("age", 18)),
        (lambda column: operator.lt(column, 18), LessThan("age", 18)),
        (lambda column: operator.le(column, 18), LessThanOrEqual("age", 18)),
    ],
)
def test_table_column_builds_all_pyiceberg_comparisons(comparison, expected):
    table, _ = make_table()

    assert comparison(table.column("age")) == expected


def test_table_column_expressions_compose_structurally():
    table, _ = make_table()

    expression = (
        (table.column("brand") == "candy or not")
        & (table.column("origin") != "north and west")
    ) | ~(table.column("notice") >= "not available")

    assert expression == Or(
        And(
            EqualTo("brand", "candy or not"),
            NotEqualTo("origin", "north and west"),
        ),
        LessThan("notice", "not available"),
    )


def test_table_column_validates_nested_names_case_sensitively():
    table, _ = make_table()

    assert table.column("profile.name").name == "profile.name"

    with pytest.raises(ValueError, match="Column Profile.name not found"):
        table.column("Profile.name")

    with pytest.raises(ValueError, match="Column profile.missing not found"):
        table.column("profile.missing")


@pytest.mark.parametrize(
    "delete_filter",
    [
        "age >= 18 AND brand = 'candy'",
        GreaterThanOrEqual("age", 18),
    ],
)
def test_delete_forwards_canonical_filters_unchanged(delete_filter):
    table, iceberg_table = make_table()

    result = table.delete(filters=delete_filter, max_retries=0)

    assert result is table
    assert len(iceberg_table.delete_calls) == 1
    assert iceberg_table.delete_calls[0]["delete_filter"] is delete_filter
    assert iceberg_table.delete_calls[0]["case_sensitive"] is True


@pytest.mark.parametrize(
    "legacy_filter",
    [
        pc.field("age") >= 18,
        [pc.field("age") >= 18, pc.field("brand") == "candy"],
    ],
)
def test_pyarrow_filters_raise_migration_error_before_write_escalation(
    monkeypatch, legacy_filter
):
    table, iceberg_table = make_table()

    def unexpected_escalation(mode):
        raise AssertionError("invalid filters must fail before credential vending")

    monkeypatch.setattr(table, "_ensure_read_write_table", unexpected_escalation)

    with pytest.raises(
        PyArrowFilterMigrationError,
        match=r'table\.column\("age"\) >= 18.*a & b',
    ):
        table.delete(legacy_filter)

    assert iceberg_table.delete_calls == []


@pytest.mark.parametrize("invalid_filter", [None, True, 42, ("age = 18",)])
def test_delete_rejects_other_filter_types_before_write_escalation(
    monkeypatch, invalid_filter
):
    table, iceberg_table = make_table()

    def unexpected_escalation(mode):
        raise AssertionError("invalid filters must fail before credential vending")

    monkeypatch.setattr(table, "_ensure_read_write_table", unexpected_escalation)

    with pytest.raises(
        TypeError,
        match="filters must be a SQL-like string or a PyIceberg BooleanExpression",
    ):
        table.delete(invalid_filter)

    assert iceberg_table.delete_calls == []
