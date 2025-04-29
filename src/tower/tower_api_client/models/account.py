from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Account")


@_attrs_define
class Account:
    """
    Attributes:
        name (str):
        slug (str):
    """

    name: str
    slug: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "slug": slug,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        slug = d.pop("slug")

        account = cls(
            name=name,
            slug=slug,
        )

        return account
