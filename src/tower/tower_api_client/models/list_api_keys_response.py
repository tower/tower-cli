from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="ListAPIKeysResponse")


@attr.s(auto_attribs=True)
class ListAPIKeysResponse:
    """
    Attributes:
        api_keys (List['APIKey']): List of API keys
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListAPIKeysResponse.json.
    """

    api_keys: List["APIKey"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        api_keys = []
        for api_keys_item_data in self.api_keys:
            api_keys_item = api_keys_item_data.to_dict()

            api_keys.append(api_keys_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "api_keys": api_keys,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = src_dict.copy()
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
