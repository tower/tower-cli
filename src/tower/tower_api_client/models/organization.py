from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """
    Attributes:
        name (str): The name of the organization
        owner (User):
    """

    name: str
    owner: User

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        owner = self.owner.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "owner": owner,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User

        d = dict(src_dict)
        name = d.pop("name")

        owner = User.from_dict(d.pop("owner"))

        organization = cls(
            name=name,
            owner=owner,
        )

        return organization
