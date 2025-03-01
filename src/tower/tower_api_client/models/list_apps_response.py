from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_summary import AppSummary
    from ..models.pagination import Pagination


T = TypeVar("T", bound="ListAppsResponse")


@attr.s(auto_attribs=True)
class ListAppsResponse:
    """
    Attributes:
        apps (List['AppSummary']):
        pages (Pagination):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListAppsResponse.json.
    """

    apps: List["AppSummary"]
    pages: "Pagination"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        apps = []
        for apps_item_data in self.apps:
            apps_item = apps_item_data.to_dict()

            apps.append(apps_item)

        pages = self.pages.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app_summary import AppSummary
        from ..models.pagination import Pagination

        d = src_dict.copy()
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
