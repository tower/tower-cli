from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteAPIKeyParams")


@_attrs_define
class DeleteAPIKeyParams:
    """
    Attributes:
        identifier (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteAPIKeyParams.json.
    """

    identifier: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "identifier": identifier,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identifier = d.pop("identifier")

        schema = d.pop("$schema", UNSET)

        delete_api_key_params = cls(
            identifier=identifier,
            schema=schema,
        )

        return delete_api_key_params
