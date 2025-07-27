from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteAuthenticatorParams")


@_attrs_define
class DeleteAuthenticatorParams:
    """
    Attributes:
        authenticator_id (str): The ID of the authenticator to delete
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteAuthenticatorParams.json.
    """

    authenticator_id: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        authenticator_id = self.authenticator_id

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "authenticator_id": authenticator_id,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        authenticator_id = d.pop("authenticator_id")

        schema = d.pop("$schema", UNSET)

        delete_authenticator_params = cls(
            authenticator_id=authenticator_id,
            schema=schema,
        )

        return delete_authenticator_params
