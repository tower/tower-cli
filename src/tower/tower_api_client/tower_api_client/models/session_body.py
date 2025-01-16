from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.token import Token
    from ..models.user import User


T = TypeVar("T", bound="SessionBody")


@_attrs_define
class SessionBody:
    """
    Attributes:
        token (Token):
        user (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    token: "Token"
    user: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        token = self.token.to_dict()

        user = self.user.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "token": token,
                "user": user,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.token import Token
        from ..models.user import User

        d = src_dict.copy()
        token = Token.from_dict(d.pop("token"))

        user = User.from_dict(d.pop("user"))

        schema = d.pop("$schema", UNSET)

        session_body = cls(
            token=token,
            user=user,
            schema=schema,
        )

        return session_body
