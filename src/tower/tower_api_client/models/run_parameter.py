from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunParameter")


@_attrs_define
class RunParameter:
    """
    Attributes:
        name (str):
        value (str):
        hidden (bool | Unset): Whether this parameter is hidden/secret. Defaults to false. Default: False.
    """

    name: str
    value: str
    hidden: bool | Unset = False

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        value = self.value

        hidden = self.hidden

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "value": value,
            }
        )
        if hidden is not UNSET:
            field_dict["hidden"] = hidden

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        value = d.pop("value")

        hidden = d.pop("hidden", UNSET)

        run_parameter = cls(
            name=name,
            value=value,
            hidden=hidden,
        )

        return run_parameter
