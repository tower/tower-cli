from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_invitation import TeamInvitation


T = TypeVar("T", bound="ResendTeamInvitationResponse")


@attr.s(auto_attribs=True)
class ResendTeamInvitationResponse:
    """
    Attributes:
        team_invitation (TeamInvitation):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ResendTeamInvitationResponse.json.
    """

    team_invitation: "TeamInvitation"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        team_invitation = self.team_invitation.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "team_invitation": team_invitation,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team_invitation import TeamInvitation

        d = src_dict.copy()
        team_invitation = TeamInvitation.from_dict(d.pop("team_invitation"))

        schema = d.pop("$schema", UNSET)

        resend_team_invitation_response = cls(
            team_invitation=team_invitation,
            schema=schema,
        )

        return resend_team_invitation_response
