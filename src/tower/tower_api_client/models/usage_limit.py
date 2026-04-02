from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UsageLimit")


@_attrs_define
class UsageLimit:
    """
    Attributes:
        limit (int): For numeric quotas: the maximum number of units allowed (-1 means unlimited). For boolean
            entitlements (e.g. self_hosted_runners): 0 = disabled, 1 = enabled.
        used (int): The number of units used for this resource.
    """

    limit: int
    used: int

    def to_dict(self) -> dict[str, Any]:
        limit = self.limit

        used = self.used

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "limit": limit,
                "used": used,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        limit = d.pop("limit")

        used = d.pop("used")

        usage_limit = cls(
            limit=limit,
            used=used,
        )

        return usage_limit
