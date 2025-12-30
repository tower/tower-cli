from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.environment import Environment
    from ..models.pagination import Pagination


T = TypeVar("T", bound="ListEnvironmentsResponse")


@_attrs_define
class ListEnvironmentsResponse:
    """
    Attributes:
        environments (list['Environment']):
        pages (Pagination):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListEnvironmentsResponse.json.
    """

    environments: list["Environment"]
    pages: "Pagination"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environments = []
        for environments_item_data in self.environments:
            environments_item = environments_item_data.to_dict()
            environments.append(environments_item)

        pages = self.pages.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environments": environments,
                "pages": pages,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.environment import Environment
        from ..models.pagination import Pagination

        d = dict(src_dict)
        environments = []
        _environments = d.pop("environments")
        for environments_item_data in _environments:
            environments_item = Environment.from_dict(environments_item_data)

            environments.append(environments_item)

        pages = Pagination.from_dict(d.pop("pages"))

        schema = d.pop("$schema", UNSET)

        list_environments_response = cls(
            environments=environments,
            pages=pages,
            schema=schema,
        )

        return list_environments_response
