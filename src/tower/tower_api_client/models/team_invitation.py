from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="TeamInvitation")


@_attrs_define
class TeamInvitation:
    """
    Attributes:
        email (str):
        invitation_sent_at (datetime.datetime):
        team (Team):
        target_organization_name (str | Unset): The name of the organization the user will move to if they accept this
            invitation
        will_change_organization (bool | Unset): Indicates if accepting this invitation will move the user to a
            different organization
    """

    email: str
    invitation_sent_at: datetime.datetime
    team: Team
    target_organization_name: str | Unset = UNSET
    will_change_organization: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        invitation_sent_at = self.invitation_sent_at.isoformat()

        team = self.team.to_dict()

        target_organization_name = self.target_organization_name

        will_change_organization = self.will_change_organization

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
                "invitation_sent_at": invitation_sent_at,
                "team": team,
            }
        )
        if target_organization_name is not UNSET:
            field_dict["target_organization_name"] = target_organization_name
        if will_change_organization is not UNSET:
            field_dict["will_change_organization"] = will_change_organization

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team

        d = dict(src_dict)
        email = d.pop("email")

        invitation_sent_at = isoparse(d.pop("invitation_sent_at"))

        team = Team.from_dict(d.pop("team"))

        target_organization_name = d.pop("target_organization_name", UNSET)

        will_change_organization = d.pop("will_change_organization", UNSET)

        team_invitation = cls(
            email=email,
            invitation_sent_at=invitation_sent_at,
            team=team,
            target_organization_name=target_organization_name,
            will_change_organization=will_change_organization,
        )

        return team_invitation
