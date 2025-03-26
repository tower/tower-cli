from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_invitation import TeamInvitation


T = TypeVar("T", bound="ListMyTeamInvitationsResponse")


@attr.s(auto_attribs=True)
class ListMyTeamInvitationsResponse:
    """
    Attributes:
        team_invitations (List['TeamInvitation']): All of team invitations
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListMyTeamInvitationsResponse.json.
    """

    team_invitations: List["TeamInvitation"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        team_invitations = []
        for team_invitations_item_data in self.team_invitations:
            team_invitations_item = team_invitations_item_data.to_dict()

            team_invitations.append(team_invitations_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "team_invitations": team_invitations,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team_invitation import TeamInvitation

        d = src_dict.copy()
        team_invitations = []
        _team_invitations = d.pop("team_invitations")
        for team_invitations_item_data in _team_invitations:
            team_invitations_item = TeamInvitation.from_dict(team_invitations_item_data)

            team_invitations.append(team_invitations_item)

        schema = d.pop("$schema", UNSET)

        list_my_team_invitations_response = cls(
            team_invitations=team_invitations,
            schema=schema,
        )

        return list_my_team_invitations_response
