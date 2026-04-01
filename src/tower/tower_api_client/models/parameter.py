from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Parameter")


@_attrs_define
class Parameter:
    """
    Attributes:
        default (str):
        description (str):
        name (str):
        hidden (bool | Unset): Whether this parameter is hidden/secret. Defaults to false. Default: False.
    """

    default: str
    description: str
    name: str
    hidden: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        default = self.default

        description = self.description

        name = self.name

        hidden = self.hidden

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "default": default,
                "description": description,
                "name": name,
            }
        )
        if hidden is not UNSET:
            field_dict["hidden"] = hidden

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        default = d.pop("default")

        description = d.pop("description")

        name = d.pop("name")

        hidden = d.pop("hidden", UNSET)

        parameter = cls(
            default=default,
            description=description,
            name=name,
            hidden=hidden,
        )

        return parameter
