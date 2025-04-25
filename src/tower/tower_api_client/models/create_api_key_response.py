from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="CreateAPIKeyResponse")


@_attrs_define
class CreateAPIKeyResponse:
    """
    Attributes:
        api_key (APIKey):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAPIKeyResponse.json.
    """

    api_key: "APIKey"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        api_key = self.api_key.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "api_key": api_key,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = dict(src_dict)
        api_key = APIKey.from_dict(d.pop("api_key"))

        schema = d.pop("$schema", UNSET)

        create_api_key_response = cls(
            api_key=api_key,
            schema=schema,
        )

        return create_api_key_response
