from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team import Team
    from ..models.team_invitation import TeamInvitation
    from ..models.user import User


T = TypeVar("T", bound="DescribeTeamResponse")


@_attrs_define
class DescribeTeamResponse:
    """
    Attributes:
        invitations (list[TeamInvitation]): Pending team invitations
        members (list[User]): The members of the team
        team (Team):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeTeamResponse.json.
    """

    invitations: list[TeamInvitation]
    members: list[User]
    team: Team
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        invitations = []
        for invitations_item_data in self.invitations:
            invitations_item = invitations_item_data.to_dict()
            invitations.append(invitations_item)

        members = []
        for members_item_data in self.members:
            members_item = members_item_data.to_dict()
            members.append(members_item)

        team = self.team.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "invitations": invitations,
                "members": members,
                "team": team,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team
        from ..models.team_invitation import TeamInvitation
        from ..models.user import User

        d = dict(src_dict)
        invitations = []
        _invitations = d.pop("invitations")
        for invitations_item_data in _invitations:
            invitations_item = TeamInvitation.from_dict(invitations_item_data)

            invitations.append(invitations_item)

        members = []
        _members = d.pop("members")
        for members_item_data in _members:
            members_item = User.from_dict(members_item_data)

            members.append(members_item)

        team = Team.from_dict(d.pop("team"))

        schema = d.pop("$schema", UNSET)

        describe_team_response = cls(
            invitations=invitations,
            members=members,
            team=team,
            schema=schema,
        )

        return describe_team_response
