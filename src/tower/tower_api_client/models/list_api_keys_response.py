from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="ListAPIKeysResponse")


@_attrs_define
class ListAPIKeysResponse:
    """
    Attributes:
        api_keys (list['APIKey']): List of API keys
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListAPIKeysResponse.json.
    """

    api_keys: list["APIKey"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        api_keys = []
        for api_keys_item_data in self.api_keys:
            api_keys_item = api_keys_item_data.to_dict()
            api_keys.append(api_keys_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "api_keys": api_keys,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = dict(src_dict)
        api_keys = []
        _api_keys = d.pop("api_keys")
        for api_keys_item_data in _api_keys:
            api_keys_item = APIKey.from_dict(api_keys_item_data)

            api_keys.append(api_keys_item)

        schema = d.pop("$schema", UNSET)

        list_api_keys_response = cls(
            api_keys=api_keys,
            schema=schema,
        )

        return list_api_keys_response
