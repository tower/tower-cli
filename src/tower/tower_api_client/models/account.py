from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="Account")


@attr.s(auto_attribs=True)
class Account:
    """
    Attributes:
        name (str):
        slug (str):
    """

    name: str
    slug: str

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        slug = self.slug

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "slug": slug,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        slug = d.pop("slug")

        account = cls(
            name=name,
            slug=slug,
        )

        return account
