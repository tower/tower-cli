from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="RunAttempt")


@_attrs_define
class RunAttempt:
    """
    Attributes:
        ended_at (datetime.datetime | None): When this attempt ended.
        exit_code (int | None): Exit code for this attempt.
        seq (int): 1-based attempt number.
        started_at (datetime.datetime | None): When the run started executing your code.
        starting_at (datetime.datetime | None): When the runner environment started to get setup.
        status (str): Terminal status of this attempt.
    """

    ended_at: datetime.datetime | None
    exit_code: int | None
    seq: int
    started_at: datetime.datetime | None
    starting_at: datetime.datetime | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        ended_at: None | str
        if isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        exit_code: int | None
        exit_code = self.exit_code

        seq = self.seq

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        starting_at: None | str
        if isinstance(self.starting_at, datetime.datetime):
            starting_at = self.starting_at.isoformat()
        else:
            starting_at = self.starting_at

        status = self.status

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "ended_at": ended_at,
                "exit_code": exit_code,
                "seq": seq,
                "started_at": started_at,
                "starting_at": starting_at,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_ended_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        ended_at = _parse_ended_at(d.pop("ended_at"))

        def _parse_exit_code(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        exit_code = _parse_exit_code(d.pop("exit_code"))

        seq = d.pop("seq")

        def _parse_started_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        started_at = _parse_started_at(d.pop("started_at"))

        def _parse_starting_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                starting_at_type_0 = isoparse(data)

                return starting_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        starting_at = _parse_starting_at(d.pop("starting_at"))

        status = d.pop("status")

        run_attempt = cls(
            ended_at=ended_at,
            exit_code=exit_code,
            seq=seq,
            started_at=started_at,
            starting_at=starting_at,
            status=status,
        )

        return run_attempt
