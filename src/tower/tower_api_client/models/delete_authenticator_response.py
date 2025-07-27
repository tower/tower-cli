from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.verified_authenticator import VerifiedAuthenticator


T = TypeVar("T", bound="DeleteAuthenticatorResponse")


@_attrs_define
class DeleteAuthenticatorResponse:
    """
    Attributes:
        authenticator (VerifiedAuthenticator):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteAuthenticatorResponse.json.
    """

    authenticator: "VerifiedAuthenticator"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        authenticator = self.authenticator.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "authenticator": authenticator,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.verified_authenticator import VerifiedAuthenticator

        d = dict(src_dict)
        authenticator = VerifiedAuthenticator.from_dict(d.pop("authenticator"))

        schema = d.pop("$schema", UNSET)

        delete_authenticator_response = cls(
            authenticator=authenticator,
            schema=schema,
        )

        return delete_authenticator_response
