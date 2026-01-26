from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.team_membership_role import TeamMembershipRole

if TYPE_CHECKING:
    from ..models.team import Team
    from ..models.user import User


T = TypeVar("T", bound="TeamMembership")


@_attrs_define
class TeamMembership:
    """
    Attributes:
        role (TeamMembershipRole):
        team (Team):
        user (User):
    """

    role: TeamMembershipRole
    team: Team
    user: User

    def to_dict(self) -> dict[str, Any]:
        role = self.role.value

        team = self.team.to_dict()

        user = self.user.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "role": role,
                "team": team,
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team
        from ..models.user import User

        d = dict(src_dict)
        role = TeamMembershipRole(d.pop("role"))

        team = Team.from_dict(d.pop("team"))

        user = User.from_dict(d.pop("user"))

        team_membership = cls(
            role=role,
            team=team,
            user=user,
        )

        return team_membership
