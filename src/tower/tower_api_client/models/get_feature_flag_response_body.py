from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.get_feature_flag_response_body_value_type import (
    GetFeatureFlagResponseBodyValueType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetFeatureFlagResponseBody")


@_attrs_define
class GetFeatureFlagResponseBody:
    """
    Attributes:
        enabled (bool): Whether the flag is enabled
        key (str): The feature flag key
        value (Any): The flag value (type depends on value_type)
        value_type (GetFeatureFlagResponseBodyValueType): The type of the value
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/GetFeatureFlagResponseBody.json.
    """

    enabled: bool
    key: str
    value: Any
    value_type: GetFeatureFlagResponseBodyValueType
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        key = self.key

        value = self.value

        value_type = self.value_type.value

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "enabled": enabled,
                "key": key,
                "value": value,
                "value_type": value_type,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled")

        key = d.pop("key")

        value = d.pop("value")

        value_type = GetFeatureFlagResponseBodyValueType(d.pop("value_type"))

        schema = d.pop("$schema", UNSET)

        get_feature_flag_response_body = cls(
            enabled=enabled,
            key=key,
            value=value,
            value_type=value_type,
            schema=schema,
        )

        return get_feature_flag_response_body
