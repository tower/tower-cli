from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_version import AppVersion


T = TypeVar("T", bound="DescribeAppVersionResponse")


@attr.s(auto_attribs=True)
class DescribeAppVersionResponse:
    """
    Attributes:
        version (AppVersion):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DescribeAppVersionResponse.json.
    """

    version: "AppVersion"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        version = self.version.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "version": version,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app_version import AppVersion

        d = src_dict.copy()
        version = AppVersion.from_dict(d.pop("version"))

        schema = d.pop("$schema", UNSET)

        describe_app_version_response = cls(
            version=version,
            schema=schema,
        )

        return describe_app_version_response
