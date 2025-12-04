from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_graph_node import RunGraphNode


T = TypeVar("T", bound="DescribeRunGraphResponse")


@_attrs_define
class DescribeRunGraphResponse:
    """
    Attributes:
        runs (list['RunGraphNode']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeRunGraphResponse.json.
    """

    runs: list["RunGraphNode"]
    schema: Union[Unset, str] = UNSET

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
        from ..models.run_graph_node import RunGraphNode

        d = dict(src_dict)
        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = RunGraphNode.from_dict(runs_item_data)

            runs.append(runs_item)

        schema = d.pop("$schema", UNSET)

        describe_run_graph_response = cls(
            runs=runs,
            schema=schema,
        )

        return describe_run_graph_response
