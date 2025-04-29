from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.token import Token


T = TypeVar("T", bound="Team")


@_attrs_define
class Team:
    """
    Attributes:
        name (str):
        slug (str):
        type_ (str): The type of team, either 'personal' or 'team'.
        token (Union[Unset, Token]):
    """

    name: str
    slug: str
    type_: str
    token: Union[Unset, "Token"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        type_ = self.type_

        token: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.token, Unset):
            token = self.token.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "slug": slug,
                "type": type_,
            }
        )
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.token import Token

        d = dict(src_dict)
        name = d.pop("name")

        slug = d.pop("slug")

        type_ = d.pop("type")

        _token = d.pop("token", UNSET)
        token: Union[Unset, Token]
        if isinstance(_token, Unset):
            token = UNSET
        else:
            token = Token.from_dict(_token)

        team = cls(
            name=name,
            slug=slug,
            type_=type_,
            token=token,
        )

        return team
