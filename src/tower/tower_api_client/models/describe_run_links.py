from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="DescribeRunLinks")


@_attrs_define
class DescribeRunLinks:
    """
    Attributes:
        next_ (None | str): The URL of the next run, if any.
        next_number (int | None): The number of the next run, if any.
        prev (None | str): The URL of the previous run, if any.
        prev_number (int | None): The number of the previous run, if any.
        self_ (str): The URL of this run.
    """

    next_: None | str
    next_number: int | None
    prev: None | str
    prev_number: int | None
    self_: str

    def to_dict(self) -> dict[str, Any]:
        next_: None | str
        next_ = self.next_

        next_number: int | None
        next_number = self.next_number

        prev: None | str
        prev = self.prev

        prev_number: int | None
        prev_number = self.prev_number

        self_ = self.self_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "next": next_,
                "next_number": next_number,
                "prev": prev,
                "prev_number": prev_number,
                "self": self_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_next_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_ = _parse_next_(d.pop("next"))

        def _parse_next_number(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        next_number = _parse_next_number(d.pop("next_number"))

        def _parse_prev(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        prev = _parse_prev(d.pop("prev"))

        def _parse_prev_number(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        prev_number = _parse_prev_number(d.pop("prev_number"))

        self_ = d.pop("self")

        describe_run_links = cls(
            next_=next_,
            next_number=next_number,
            prev=prev,
            prev_number=prev_number,
            self_=self_,
        )

        return describe_run_links
