from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Account")


@_attrs_define
class Account:
    """
    Attributes:
        is_self_hosted_only (bool):
        name (str):
        slug (str | Unset): This property is deprecated. Use name instead.
    """

    is_self_hosted_only: bool
    name: str
    slug: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        is_self_hosted_only = self.is_self_hosted_only

        name = self.name

        slug = self.slug

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "is_self_hosted_only": is_self_hosted_only,
                "name": name,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_self_hosted_only = d.pop("is_self_hosted_only")

        name = d.pop("name")

        slug = d.pop("slug", UNSET)

        account = cls(
            is_self_hosted_only=is_self_hosted_only,
            name=name,
            slug=slug,
        )

        return account
