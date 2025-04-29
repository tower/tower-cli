from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_invitation import TeamInvitation


T = TypeVar("T", bound="ListMyTeamInvitationsResponse")


@_attrs_define
class ListMyTeamInvitationsResponse:
    """
    Attributes:
        team_invitations (list['TeamInvitation']): All of team invitations
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListMyTeamInvitationsResponse.json.
    """

    team_invitations: list["TeamInvitation"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        team_invitations = []
        for team_invitations_item_data in self.team_invitations:
            team_invitations_item = team_invitations_item_data.to_dict()
            team_invitations.append(team_invitations_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "team_invitations": team_invitations,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team_invitation import TeamInvitation

        d = dict(src_dict)
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
