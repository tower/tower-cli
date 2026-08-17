from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunLinks")


@_attrs_define
class RunLinks:
    """
    Attributes:
        next_number (int | None): The number of the next run, if any.
        prev_number (int | None): The number of the previous run, if any.
    """

    next_number: int | None
    prev_number: int | None

    def to_dict(self) -> dict[str, Any]:
        next_number: int | None
        next_number = self.next_number

        prev_number: int | None
        prev_number = self.prev_number

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "next_number": next_number,
                "prev_number": prev_number,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_next_number(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        next_number = _parse_next_number(d.pop("next_number"))

        def _parse_prev_number(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        prev_number = _parse_prev_number(d.pop("prev_number"))

        run_links = cls(
            next_number=next_number,
            prev_number=prev_number,
        )

        return run_links
