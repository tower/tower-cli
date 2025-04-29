from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="InviteTeamMemberParams")


@_attrs_define
class InviteTeamMemberParams:
    """
    Attributes:
        emails (str): The email addresses of the people to invite. It can be a list in any format (comma separated,
            newline separated, etc.) and it will be parsed into individual addresses
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/InviteTeamMemberParams.json.
        message (Union[Unset, str]): Optional message to include in the invite email
    """

    emails: str
    schema: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        emails = self.emails

        schema = self.schema

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "emails": emails,
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
        emails = d.pop("emails")

        schema = d.pop("$schema", UNSET)

        message = d.pop("message", UNSET)

        invite_team_member_params = cls(
            emails=emails,
            schema=schema,
            message=message,
        )

        return invite_team_member_params
