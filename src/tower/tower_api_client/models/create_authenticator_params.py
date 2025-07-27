from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAuthenticatorParams")


@_attrs_define
class CreateAuthenticatorParams:
    """
    Attributes:
        authenticator_url (str): The authenticator URL with an otpauth scheme that identifies this authenticator
        verification_code (str): A code taken from the authenticator as verification that it's correctly configured.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAuthenticatorParams.json.
    """

    authenticator_url: str
    verification_code: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        authenticator_url = self.authenticator_url

        verification_code = self.verification_code

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "authenticator_url": authenticator_url,
                "verification_code": verification_code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        authenticator_url = d.pop("authenticator_url")

        verification_code = d.pop("verification_code")

        schema = d.pop("$schema", UNSET)

        create_authenticator_params = cls(
            authenticator_url=authenticator_url,
            verification_code=verification_code,
            schema=schema,
        )

        return create_authenticator_params
