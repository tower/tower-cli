from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAPIKeyParams")


@attr.s(auto_attribs=True)
class CreateAPIKeyParams:
    """
    Attributes:
        name (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateAPIKeyParams.json.
    """

    name: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        create_api_key_params = cls(
            name=name,
            schema=schema,
        )

        return create_api_key_params
