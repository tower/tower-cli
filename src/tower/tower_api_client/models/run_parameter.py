from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

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
        is_override (bool | None | Unset): Whether this parameter's value was supplied as an override at run/schedule
            creation time (true) or comes from the app version's default (false).
    """

    name: str
    value: str
    hidden: bool | Unset = False
    is_override: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        value = self.value

        hidden = self.hidden

        is_override: bool | None | Unset
        if isinstance(self.is_override, Unset):
            is_override = UNSET
        else:
            is_override = self.is_override

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "value": value,
            }
        )
        if hidden is not UNSET:
            field_dict["hidden"] = hidden
        if is_override is not UNSET:
            field_dict["is_override"] = is_override

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        value = d.pop("value")

        hidden = d.pop("hidden", UNSET)

        def _parse_is_override(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_override = _parse_is_override(d.pop("is_override", UNSET))

        run_parameter = cls(
            name=name,
            value=value,
            hidden=hidden,
            is_override=is_override,
        )

        return run_parameter
