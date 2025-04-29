from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResendTeamInvitationParams")


@_attrs_define
class ResendTeamInvitationParams:
    """
    Attributes:
        email (str): The email address of team invitation to resend
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ResendTeamInvitationParams.json.
        message (Union[Unset, str]): Optional message to include in the invite email
    """

    email: str
    schema: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        schema = self.schema

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "email": email,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        schema = d.pop("$schema", UNSET)

        message = d.pop("message", UNSET)

        resend_team_invitation_params = cls(
            email=email,
            schema=schema,
            message=message,
        )

        return resend_team_invitation_params
