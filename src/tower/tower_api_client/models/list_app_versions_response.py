from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_version import AppVersion


T = TypeVar("T", bound="ListAppVersionsResponse")


@attr.s(auto_attribs=True)
class ListAppVersionsResponse:
    """
    Attributes:
        versions (List['AppVersion']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListAppVersionsResponse.json.
    """

    versions: List["AppVersion"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()

            versions.append(versions_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "versions": versions,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app_version import AppVersion

        d = src_dict.copy()
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
