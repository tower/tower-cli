from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_summary import AppSummary
    from ..models.pagination import Pagination


T = TypeVar("T", bound="GetAppsOutputBody")


@_attrs_define
class GetAppsOutputBody:
    """
    Attributes:
        apps (Union[None, list['AppSummary']]):
        pages (Pagination):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    apps: Union[None, list["AppSummary"]]
    pages: "Pagination"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        apps: Union[None, list[dict[str, Any]]]
        if isinstance(self.apps, list):
            apps = []
            for apps_type_0_item_data in self.apps:
                apps_type_0_item = apps_type_0_item_data.to_dict()
                apps.append(apps_type_0_item)

        else:
            apps = self.apps

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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.app_summary import AppSummary
        from ..models.pagination import Pagination

        d = src_dict.copy()

        def _parse_apps(data: object) -> Union[None, list["AppSummary"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                apps_type_0 = []
                _apps_type_0 = data
                for apps_type_0_item_data in _apps_type_0:
                    apps_type_0_item = AppSummary.from_dict(apps_type_0_item_data)

                    apps_type_0.append(apps_type_0_item)

                return apps_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["AppSummary"]], data)

        apps = _parse_apps(d.pop("apps"))

        pages = Pagination.from_dict(d.pop("pages"))

        schema = d.pop("$schema", UNSET)

        get_apps_output_body = cls(
            apps=apps,
            pages=pages,
            schema=schema,
        )

        return get_apps_output_body
