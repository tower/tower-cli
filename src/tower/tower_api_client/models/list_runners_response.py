from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.runner import Runner


T = TypeVar("T", bound="ListRunnersResponse")


@_attrs_define
class ListRunnersResponse:
    """
    Attributes:
        pages (Pagination):
        runners (list['Runner']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListRunnersResponse.json.
    """

    pages: "Pagination"
    runners: list["Runner"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        runners = []
        for runners_item_data in self.runners:
            runners_item = runners_item_data.to_dict()
            runners.append(runners_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "pages": pages,
                "runners": runners,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.runner import Runner

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        runners = []
        _runners = d.pop("runners")
        for runners_item_data in _runners:
            runners_item = Runner.from_dict(runners_item_data)

            runners.append(runners_item)

        schema = d.pop("$schema", UNSET)

        list_runners_response = cls(
            pages=pages,
            runners=runners,
            schema=schema,
        )

        return list_runners_response
