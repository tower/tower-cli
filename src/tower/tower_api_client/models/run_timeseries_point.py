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
        running (int):
        scheduled (int):
    """

    cancelled: int
    crashed: int
    errored: int
    exited: int
    pending: int
    period: datetime.datetime
    running: int
    scheduled: int

    def to_dict(self) -> dict[str, Any]:
        cancelled = self.cancelled

        crashed = self.crashed

        errored = self.errored

        exited = self.exited

        pending = self.pending

        period = self.period.isoformat()

        running = self.running

        scheduled = self.scheduled

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "cancelled": cancelled,
                "crashed": crashed,
                "errored": errored,
                "exited": exited,
                "pending": pending,
                "period": period,
                "running": running,
                "scheduled": scheduled,
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

        running = d.pop("running")

        scheduled = d.pop("scheduled")

        run_timeseries_point = cls(
            cancelled=cancelled,
            crashed=crashed,
            errored=errored,
            exited=exited,
            pending=pending,
            period=period,
            running=running,
            scheduled=scheduled,
        )

        return run_timeseries_point
