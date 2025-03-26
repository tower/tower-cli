from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.token import Token


T = TypeVar("T", bound="Team")


@attr.s(auto_attribs=True)
class Team:
    """
    Attributes:
        name (str):
        slug (str):
        type (str): The type of team, either 'personal' or 'team'.
        token (Union[Unset, Token]):
    """

    name: str
    slug: str
    type: str
    token: Union[Unset, "Token"] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        slug = self.slug
        type = self.type
        token: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.token, Unset):
            token = self.token.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "slug": slug,
                "type": type,
            }
        )
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.token import Token

        d = src_dict.copy()
        name = d.pop("name")

        slug = d.pop("slug")

        type = d.pop("type")

        _token = d.pop("token", UNSET)
        token: Union[Unset, Token]
        if isinstance(_token, Unset):
            token = UNSET
        else:
            token = Token.from_dict(_token)

        team = cls(
            name=name,
            slug=slug,
            type=type,
            token=token,
        )

        return team
