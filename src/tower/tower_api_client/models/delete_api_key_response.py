from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key import APIKey


T = TypeVar("T", bound="DeleteAPIKeyResponse")


@attr.s(auto_attribs=True)
class DeleteAPIKeyResponse:
    """
    Attributes:
        api_key (APIKey):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DeleteAPIKeyResponse.json.
    """

    api_key: "APIKey"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        api_key = self.api_key.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "api_key": api_key,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.api_key import APIKey

        d = src_dict.copy()
        api_key = APIKey.from_dict(d.pop("api_key"))

        schema = d.pop("$schema", UNSET)

        delete_api_key_response = cls(
            api_key=api_key,
            schema=schema,
        )

        return delete_api_key_response
