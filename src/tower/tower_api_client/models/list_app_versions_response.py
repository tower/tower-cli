from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_version import AppVersion


T = TypeVar("T", bound="ListAppVersionsResponse")


@_attrs_define
class ListAppVersionsResponse:
    """
    Attributes:
        versions (list['AppVersion']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListAppVersionsResponse.json.
    """

    versions: list["AppVersion"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "versions": versions,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_version import AppVersion

        d = dict(src_dict)
        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = AppVersion.from_dict(versions_item_data)

            versions.append(versions_item)

        schema = d.pop("$schema", UNSET)

        list_app_versions_response = cls(
            versions=versions,
            schema=schema,
        )

        return list_app_versions_response
