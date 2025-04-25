from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_version import AppVersion


T = TypeVar("T", bound="DeployAppResponse")


@_attrs_define
class DeployAppResponse:
    """
    Attributes:
        version (AppVersion):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeployAppResponse.json.
    """

    version: "AppVersion"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        version = self.version.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "version": version,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_version import AppVersion

        d = dict(src_dict)
        version = AppVersion.from_dict(d.pop("version"))

        schema = d.pop("$schema", UNSET)

        deploy_app_response = cls(
            version=version,
            schema=schema,
        )

        return deploy_app_response
