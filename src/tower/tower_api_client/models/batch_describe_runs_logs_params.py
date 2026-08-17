from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchDescribeRunsLogsParams")


@_attrs_define
class BatchDescribeRunsLogsParams:
    """
    Attributes:
        name (str): The name of the app to describe the run for.
        seq (int): The number of the run to describe.
        head (int | None | Unset): Return only the first N log lines. Cannot be combined with tail.
        start_at (datetime.datetime | None | Unset): Fetch logs from this timestamp onwards (inclusive).
        tail (int | None | Unset): Return only the last N log lines. Cannot be combined with head.
    """

    name: str
    seq: int
    head: int | None | Unset = UNSET
    start_at: datetime.datetime | None | Unset = UNSET
    tail: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        seq = self.seq

        head: int | None | Unset
        if isinstance(self.head, Unset):
            head = UNSET
        else:
            head = self.head

        start_at: None | str | Unset
        if isinstance(self.start_at, Unset):
            start_at = UNSET
        elif isinstance(self.start_at, datetime.datetime):
            start_at = self.start_at.isoformat()
        else:
            start_at = self.start_at

        tail: int | None | Unset
        if isinstance(self.tail, Unset):
            tail = UNSET
        else:
            tail = self.tail

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "seq": seq,
            }
        )
        if head is not UNSET:
            field_dict["head"] = head
        if start_at is not UNSET:
            field_dict["start_at"] = start_at
        if tail is not UNSET:
            field_dict["tail"] = tail

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        seq = d.pop("seq")

        def _parse_head(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        head = _parse_head(d.pop("head", UNSET))

        def _parse_start_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_at_type_0 = isoparse(data)

                return start_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        start_at = _parse_start_at(d.pop("start_at", UNSET))

        def _parse_tail(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        tail = _parse_tail(d.pop("tail", UNSET))

        batch_describe_runs_logs_params = cls(
            name=name,
            seq=seq,
            head=head,
            start_at=start_at,
            tail=tail,
        )

        return batch_describe_runs_logs_params
