import datetime
from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="TeamInvitation")


@attr.s(auto_attribs=True)
class TeamInvitation:
    """
    Attributes:
        email (str):
        invitation_sent_at (datetime.datetime):
        team (Team):
    """

    email: str
    invitation_sent_at: datetime.datetime
    team: "Team"

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        invitation_sent_at = self.invitation_sent_at.isoformat()

        team = self.team.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "email": email,
                "invitation_sent_at": invitation_sent_at,
                "team": team,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team import Team

        d = src_dict.copy()
        email = d.pop("email")

        invitation_sent_at = isoparse(d.pop("invitation_sent_at"))

        team = Team.from_dict(d.pop("team"))

        team_invitation = cls(
            email=email,
            invitation_sent_at=invitation_sent_at,
            team=team,
        )

        return team_invitation
