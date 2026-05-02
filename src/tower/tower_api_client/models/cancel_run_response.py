from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="CancelRunResponse")


@_attrs_define
class CancelRunResponse:
    """
    Attributes:
        cancelled_child_runs (int): Number of descendant runs that were also cancelled as part of this cascade.
        run (Run):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CancelRunResponse.json.
    """

    cancelled_child_runs: int
    run: Run
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        cancelled_child_runs = self.cancelled_child_runs

        run = self.run.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cancelled_child_runs": cancelled_child_runs,
                "run": run,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run

        d = dict(src_dict)
        cancelled_child_runs = d.pop("cancelled_child_runs")

        run = Run.from_dict(d.pop("run"))

        schema = d.pop("$schema", UNSET)

        cancel_run_response = cls(
            cancelled_child_runs=cancelled_child_runs,
            run=run,
            schema=schema,
        )

        return cancel_run_response
