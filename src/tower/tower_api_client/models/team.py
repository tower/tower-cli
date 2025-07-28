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
        type_ (str): The type of team, either 'personal' or 'team'.
        slug (Union[Unset, str]): This property is deprecated. Please use name instead.
        token (Union[Unset, Token]):
    """

    name: str
    type_: str
    slug: Union[Unset, str] = UNSET
    token: Union[Unset, "Token"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_

        slug = self.slug

        token: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.token, Unset):
            token = self.token.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "type": type_,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.token import Token

        d = dict(src_dict)
        name = d.pop("name")

        type_ = d.pop("type")

        slug = d.pop("slug", UNSET)

        _token = d.pop("token", UNSET)
        token: Union[Unset, Token]
        if isinstance(_token, Unset):
            token = UNSET
        else:
            token = Token.from_dict(_token)

        team = cls(
            name=name,
            type_=type_,
            slug=slug,
            token=token,
        )

        return team
