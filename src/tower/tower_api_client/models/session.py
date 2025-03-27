from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.team import Team
    from ..models.token import Token
    from ..models.user import User


T = TypeVar("T", bound="Session")


@attr.s(auto_attribs=True)
class Session:
    """
    Attributes:
        teams (List['Team']):
        token (Token):
        user (User):
    """

    teams: List["Team"]
    token: "Token"
    user: "User"

    def to_dict(self) -> Dict[str, Any]:
        teams = []
        for teams_item_data in self.teams:
            teams_item = teams_item_data.to_dict()

            teams.append(teams_item)

        token = self.token.to_dict()

        user = self.user.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "teams": teams,
                "token": token,
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team import Team
        from ..models.token import Token
        from ..models.user import User

        d = src_dict.copy()
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
