from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResendTeamInvitationParams")


@attr.s(auto_attribs=True)
class ResendTeamInvitationParams:
    """
    Attributes:
        email (str): The email address of team invitation to resend
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ResendTeamInvitationParams.json.
        message (Union[Unset, str]): Optional message to include in the invite email
    """

    email: str
    schema: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        schema = self.schema
        message = self.message

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        schema = d.pop("$schema", UNSET)

        message = d.pop("message", UNSET)

        resend_team_invitation_params = cls(
            email=email,
            schema=schema,
            message=message,
        )

        return resend_team_invitation_params
