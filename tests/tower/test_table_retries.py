from types import SimpleNamespace

import httpx
import pyarrow as pa
import pytest
from pyiceberg.exceptions import (
    AuthorizationExpiredError,
    BadRequestError,
    CommitFailedException,
    CommitStateUnknownException,
    ForbiddenError,
    NoSuchTableError,
    ServerError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationException,
    WaitingForLockException,
)

import tower._tables as tables_module
from tower._context import TowerContext


class FakeMutationTable:
    def __init__(self, failures=(), refresh_error=None):
        self.failures = list(failures)
        self.refresh_error = refresh_error
        self.mutations = []
        self.refresh_calls = 0
        self.events = []

    def _mutate(self, operation):
        self.mutations.append(operation)
        self.events.append(("mutation", operation))
        if self.failures:
            raise self.failures.pop(0)
        return SimpleNamespace(rows_inserted=1, rows_updated=2)

    def append(self, data):
        return self._mutate("insert")

    def upsert(self, data, **kwargs):
        return self._mutate("upsert")

    def delete(self, **kwargs):
        return self._mutate("delete")

    def refresh(self):
        self.refresh_calls += 1
        self.events.append(("refresh",))
        if self.refresh_error is not None:
            raise self.refresh_error


def make_table(iceberg_table):
    context = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
    )
    return tables_module.Table(context, iceberg_table)


def run_mutation(table, operation, max_retries, retry_delay_seconds):
    if operation == "insert":
        return table.insert(
            pa.table({"id": [1, 2, 3]}),
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
    if operation == "upsert":
        return table.upsert(
            pa.table({"id": [1, 2, 3]}),
            join_cols=["id"],
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
    if operation == "delete":
        return table.delete(
            "id = 1",
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
    raise AssertionError(f"unknown operation: {operation}")


@pytest.mark.parametrize(
    ("operation", "expected_inserts", "expected_updates"),
    [
        ("insert", 3, 0),
        ("upsert", 1, 2),
        ("delete", 0, 0),
    ],
)
def test_mutations_retry_commit_conflicts_with_exponential_full_jitter(
    monkeypatch, operation, expected_inserts, expected_updates
):
    iceberg_table = FakeMutationTable(
        [CommitFailedException("conflict 1"), CommitFailedException("conflict 2")]
    )
    table = make_table(iceberg_table)
    uniform_calls = []
    sleep_calls = []

    def uniform(low, high):
        uniform_calls.append((low, high))
        iceberg_table.events.append(("jitter", low, high))
        return high / 2

    def sleep(delay):
        sleep_calls.append(delay)
        iceberg_table.events.append(("sleep", delay))

    monkeypatch.setattr(tables_module.random, "uniform", uniform)
    monkeypatch.setattr(tables_module.time, "sleep", sleep)

    result = run_mutation(table, operation, max_retries=2, retry_delay_seconds=0.5)

    assert result is table
    assert iceberg_table.mutations == [operation, operation, operation]
    assert iceberg_table.refresh_calls == 2
    assert uniform_calls == [(0.0, 0.5), (0.0, 1.0)]
    assert sleep_calls == [0.25, 0.5]
    assert iceberg_table.events == [
        ("mutation", operation),
        ("jitter", 0.0, 0.5),
        ("sleep", 0.25),
        ("refresh",),
        ("mutation", operation),
        ("jitter", 0.0, 1.0),
        ("sleep", 0.5),
        ("refresh",),
        ("mutation", operation),
    ]
    assert table.rows_affected() == tables_module.RowsAffectedInformation(
        inserts=expected_inserts,
        updates=expected_updates,
    )


def test_commit_retry_backoff_is_capped(monkeypatch):
    iceberg_table = FakeMutationTable(
        [CommitFailedException(f"conflict {attempt}") for attempt in range(5)]
    )
    table = make_table(iceberg_table)
    uniform_calls = []

    def uniform(low, high):
        uniform_calls.append((low, high))
        return 0.0

    monkeypatch.setattr(tables_module.random, "uniform", uniform)
    monkeypatch.setattr(tables_module.time, "sleep", lambda delay: None)

    table.insert(pa.table({"id": [1]}), max_retries=5, retry_delay_seconds=10.0)

    assert uniform_calls == [
        (0.0, 10.0),
        (0.0, 20.0),
        (0.0, 30.0),
        (0.0, 30.0),
        (0.0, 30.0),
    ]


def test_commit_retry_initial_ceiling_is_clamped(monkeypatch):
    iceberg_table = FakeMutationTable([CommitFailedException("conflict")])
    table = make_table(iceberg_table)
    uniform_calls = []

    def uniform(low, high):
        uniform_calls.append((low, high))
        return 0.0

    monkeypatch.setattr(tables_module.random, "uniform", uniform)
    monkeypatch.setattr(tables_module.time, "sleep", lambda delay: None)

    table.insert(pa.table({"id": [1]}), max_retries=1, retry_delay_seconds=300.0)

    assert uniform_calls == [(0.0, 30.0)]


@pytest.mark.parametrize("max_retries", [0, 2])
def test_commit_retry_exhaustion_preserves_final_exception(monkeypatch, max_retries):
    failures = [
        CommitFailedException(f"conflict {attempt}")
        for attempt in range(max_retries + 1)
    ]
    iceberg_table = FakeMutationTable(failures)
    table = make_table(iceberg_table)
    sleep_calls = []

    monkeypatch.setattr(tables_module.random, "uniform", lambda low, high: 0.0)
    monkeypatch.setattr(tables_module.time, "sleep", sleep_calls.append)

    with pytest.raises(CommitFailedException) as exc_info:
        table.insert(
            pa.table({"id": [1]}),
            max_retries=max_retries,
            retry_delay_seconds=0.5,
        )

    assert exc_info.value is failures[-1]
    assert iceberg_table.mutations == ["insert"] * (max_retries + 1)
    assert iceberg_table.refresh_calls == max_retries
    assert len(sleep_calls) == max_retries
    assert table.rows_affected().inserts == 0


@pytest.mark.parametrize(
    "exception_type",
    [
        CommitStateUnknownException,
        ServiceUnavailableError,
        AuthorizationExpiredError,
        UnauthorizedError,
        ForbiddenError,
        NoSuchTableError,
        ServerError,
        BadRequestError,
        WaitingForLockException,
        ValidationException,
        httpx.TimeoutException,
        httpx.ConnectError,
        ValueError,
    ],
)
def test_non_retryable_mutation_errors_are_not_retried(monkeypatch, exception_type):
    failure = exception_type("not retryable")
    iceberg_table = FakeMutationTable([failure])
    table = make_table(iceberg_table)

    def unexpected_call(*args, **kwargs):
        raise AssertionError("non-retryable errors must not back off")

    monkeypatch.setattr(tables_module.random, "uniform", unexpected_call)
    monkeypatch.setattr(tables_module.time, "sleep", unexpected_call)

    with pytest.raises(exception_type) as exc_info:
        table.insert(
            pa.table({"id": [1]}),
            max_retries=5,
            retry_delay_seconds=0.5,
        )

    assert exc_info.value is failure
    assert iceberg_table.mutations == ["insert"]
    assert iceberg_table.refresh_calls == 0
    assert table.rows_affected().inserts == 0


def test_refresh_failure_is_not_retried(monkeypatch):
    refresh_failure = RuntimeError("refresh failed")
    iceberg_table = FakeMutationTable(
        [CommitFailedException("conflict")], refresh_error=refresh_failure
    )
    table = make_table(iceberg_table)

    monkeypatch.setattr(tables_module.random, "uniform", lambda low, high: 0.0)
    monkeypatch.setattr(tables_module.time, "sleep", lambda delay: None)

    with pytest.raises(RuntimeError) as exc_info:
        table.insert(
            pa.table({"id": [1]}),
            max_retries=5,
            retry_delay_seconds=0.5,
        )

    assert exc_info.value is refresh_failure
    assert iceberg_table.mutations == ["insert"]
    assert iceberg_table.refresh_calls == 1
    assert table.rows_affected().inserts == 0


@pytest.mark.parametrize(
    "retry_delay_seconds", [float("nan"), float("inf"), float("-inf")]
)
def test_commit_retry_rejects_non_finite_delay(retry_delay_seconds):
    iceberg_table = FakeMutationTable()
    table = make_table(iceberg_table)

    with pytest.raises(ValueError, match="must be finite and >= 0"):
        table.insert(pa.table({"id": [1]}), retry_delay_seconds=retry_delay_seconds)

    assert iceberg_table.mutations == []
