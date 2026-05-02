from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunResults")


@_attrs_define
class RunResults:
    """
    Attributes:
        cancelled (int):
        crashed (int):
        errored (int):
        exited (int):
        pending (int):
        retrying (int):
        running (int):
        starting (int):
    """

    cancelled: int
    crashed: int
    errored: int
    exited: int
    pending: int
    retrying: int
    running: int
    starting: int

    def to_dict(self) -> dict[str, Any]:
        cancelled = self.cancelled

        crashed = self.crashed

        errored = self.errored

        exited = self.exited

        pending = self.pending

        retrying = self.retrying

        running = self.running

        starting = self.starting

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "cancelled": cancelled,
                "crashed": crashed,
                "errored": errored,
                "exited": exited,
                "pending": pending,
                "retrying": retrying,
                "running": running,
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

        retrying = d.pop("retrying")

        running = d.pop("running")

        starting = d.pop("starting")

        run_results = cls(
            cancelled=cancelled,
            crashed=crashed,
            errored=errored,
            exited=exited,
            pending=pending,
            retrying=retrying,
            running=running,
            starting=starting,
        )

        return run_results
