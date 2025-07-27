from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreatePasswordResetParams")


@_attrs_define
class CreatePasswordResetParams:
    """
    Attributes:
        email (str): The email address to send the password reset email to
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreatePasswordResetParams.json.
    """

    email: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "email": email,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        schema = d.pop("$schema", UNSET)

        create_password_reset_params = cls(
            email=email,
            schema=schema,
        )

        return create_password_reset_params
