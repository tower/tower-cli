from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="RunTimeseriesPoint")


@_attrs_define
class RunTimeseriesPoint:
    """
    Attributes:
        cancelled (int):
        crashed (int):
        errored (int):
        exited (int):
        pending (int):
        period (datetime.datetime): The period of the timeseries point, typically the start of the period.
        retrying (int):
        running (int):
        scheduled (int):
        starting (int):
    """

    cancelled: int
    crashed: int
    errored: int
    exited: int
    pending: int
    period: datetime.datetime
    retrying: int
    running: int
    scheduled: int
    starting: int

    def to_dict(self) -> dict[str, Any]:
        cancelled = self.cancelled

        crashed = self.crashed

        errored = self.errored

        exited = self.exited

        pending = self.pending

        period = self.period.isoformat()

        retrying = self.retrying

        running = self.running

        scheduled = self.scheduled

        starting = self.starting

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cancelled": cancelled,
                "crashed": crashed,
                "errored": errored,
                "exited": exited,
                "pending": pending,
                "period": period,
                "retrying": retrying,
                "running": running,
                "scheduled": scheduled,
                "starting": starting,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cancelled = d.pop("cancelled")

        crashed = d.pop("crashed")

        errored = d.pop("errored")

        exited = d.pop("exited")

        pending = d.pop("pending")

        period = isoparse(d.pop("period"))

        retrying = d.pop("retrying")

        running = d.pop("running")

        scheduled = d.pop("scheduled")

        starting = d.pop("starting")

        run_timeseries_point = cls(
            cancelled=cancelled,
            crashed=crashed,
            errored=errored,
            exited=exited,
            pending=pending,
            period=period,
            retrying=retrying,
            running=running,
            scheduled=scheduled,
            starting=starting,
        )

        return run_timeseries_point
