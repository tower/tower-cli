from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_run_and_links import BatchRunAndLinks


T = TypeVar("T", bound="BatchDescribeRunsResponse")


@_attrs_define
class BatchDescribeRunsResponse:
    """
    Attributes:
        runs (list[BatchRunAndLinks]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/BatchDescribeRunsResponse.json.
    """

    runs: list[BatchRunAndLinks]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()
            runs.append(runs_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "runs": runs,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_run_and_links import BatchRunAndLinks

        d = dict(src_dict)
        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = BatchRunAndLinks.from_dict(runs_item_data)

            runs.append(runs_item)

        schema = d.pop("$schema", UNSET)

        batch_describe_runs_response = cls(
            runs=runs,
            schema=schema,
        )

        return batch_describe_runs_response
