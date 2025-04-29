from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.run import Run


T = TypeVar("T", bound="ListRunsResponse")


@_attrs_define
class ListRunsResponse:
    """
    Attributes:
        pages (Pagination):
        runs (list['Run']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListRunsResponse.json.
    """

    pages: "Pagination"
    runs: list["Run"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()
            runs.append(runs_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "pages": pages,
                "runs": runs,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.run import Run

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = Run.from_dict(runs_item_data)

            runs.append(runs_item)

        schema = d.pop("$schema", UNSET)

        list_runs_response = cls(
            pages=pages,
            runs=runs,
            schema=schema,
        )

        return list_runs_response
