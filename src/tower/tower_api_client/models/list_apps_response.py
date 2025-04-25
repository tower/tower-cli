from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_summary import AppSummary
    from ..models.pagination import Pagination


T = TypeVar("T", bound="ListAppsResponse")


@_attrs_define
class ListAppsResponse:
    """
    Attributes:
        apps (list['AppSummary']):
        pages (Pagination):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListAppsResponse.json.
    """

    apps: list["AppSummary"]
    pages: "Pagination"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        apps = []
        for apps_item_data in self.apps:
            apps_item = apps_item_data.to_dict()
            apps.append(apps_item)

        pages = self.pages.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "apps": apps,
                "pages": pages,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_summary import AppSummary
        from ..models.pagination import Pagination

        d = dict(src_dict)
        apps = []
        _apps = d.pop("apps")
        for apps_item_data in _apps:
            apps_item = AppSummary.from_dict(apps_item_data)

            apps.append(apps_item)

        pages = Pagination.from_dict(d.pop("pages"))

        schema = d.pop("$schema", UNSET)

        list_apps_response = cls(
            apps=apps,
            pages=pages,
            schema=schema,
        )

        return list_apps_response
