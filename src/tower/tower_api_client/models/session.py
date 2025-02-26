from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.token import Token
    from ..models.user import User


T = TypeVar("T", bound="Session")


@attr.s(auto_attribs=True)
class Session:
    """
    Attributes:
        token (Token):
        user (User):
    """

    token: "Token"
    user: "User"

    def to_dict(self) -> Dict[str, Any]:
        token = self.token.to_dict()

        user = self.user.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "token": token,
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.token import Token
        from ..models.user import User

        d = src_dict.copy()
        token = Token.from_dict(d.pop("token"))

        user = User.from_dict(d.pop("user"))

        session = cls(
            token=token,
            user=user,
        )

        return session
