from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteAPIKeyParams")


@attr.s(auto_attribs=True)
class DeleteAPIKeyParams:
    """
    Attributes:
        identifier (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DeleteAPIKeyParams.json.
    """

    identifier: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        identifier = self.identifier
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "identifier": identifier,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        identifier = d.pop("identifier")

        schema = d.pop("$schema", UNSET)

        delete_api_key_params = cls(
            identifier=identifier,
            schema=schema,
        )

        return delete_api_key_params
