from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="TeamInvitation")


@_attrs_define
class TeamInvitation:
    """
    Attributes:
        email (str):
        invitation_sent_at (datetime.datetime):
        role (str):
        team (Team):
    """

    email: str
    invitation_sent_at: datetime.datetime
    role: str
    team: Team

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        invitation_sent_at = self.invitation_sent_at.isoformat()

        role = self.role

        team = self.team.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
                "invitation_sent_at": invitation_sent_at,
                "role": role,
                "team": team,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team

        d = dict(src_dict)
        email = d.pop("email")

        invitation_sent_at = isoparse(d.pop("invitation_sent_at"))

        role = d.pop("role")

        team = Team.from_dict(d.pop("team"))

        team_invitation = cls(
            email=email,
            invitation_sent_at=invitation_sent_at,
            role=role,
            team=team,
        )

        return team_invitation
