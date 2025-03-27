from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_invitation import TeamInvitation


T = TypeVar("T", bound="DeleteTeamInvitationResponse")


@attr.s(auto_attribs=True)
class DeleteTeamInvitationResponse:
    """
    Attributes:
        invitation (TeamInvitation):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DeleteTeamInvitationResponse.json.
    """

    invitation: "TeamInvitation"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        invitation = self.invitation.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "invitation": invitation,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team_invitation import TeamInvitation

        d = src_dict.copy()
        invitation = TeamInvitation.from_dict(d.pop("invitation"))

        schema = d.pop("$schema", UNSET)

        delete_team_invitation_response = cls(
            invitation=invitation,
            schema=schema,
        )

        return delete_team_invitation_response
