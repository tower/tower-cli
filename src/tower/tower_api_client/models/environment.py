from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Environment")


@_attrs_define
class Environment:
    """
    Attributes:
        is_deletable (bool): If this environment is able to be deleted.
        name (str): The human readable name for the environment
    """

    is_deletable: bool
    name: str

    def to_dict(self) -> dict[str, Any]:
        is_deletable = self.is_deletable

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "is_deletable": is_deletable,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_deletable = d.pop("is_deletable")

        name = d.pop("name")

        environment = cls(
            is_deletable=is_deletable,
            name=name,
        )

        return environment
