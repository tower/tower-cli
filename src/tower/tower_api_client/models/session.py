from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.team import Team
    from ..models.token import Token
    from ..models.user import User


T = TypeVar("T", bound="Session")


@_attrs_define
class Session:
    """
    Attributes:
        teams (list['Team']):
        token (Token):
        user (User):
    """

    teams: list["Team"]
    token: "Token"
    user: "User"

    def to_dict(self) -> dict[str, Any]:
        teams = []
        for teams_item_data in self.teams:
            teams_item = teams_item_data.to_dict()
            teams.append(teams_item)

        token = self.token.to_dict()

        user = self.user.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "teams": teams,
                "token": token,
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team
        from ..models.token import Token
        from ..models.user import User

        d = dict(src_dict)
        teams = []
        _teams = d.pop("teams")
        for teams_item_data in _teams:
            teams_item = Team.from_dict(teams_item_data)

            teams.append(teams_item)

        token = Token.from_dict(d.pop("token"))

        user = User.from_dict(d.pop("user"))

        session = cls(
            teams=teams,
            token=token,
            user=user,
        )

        return session
