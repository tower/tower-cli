from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="RunResults")


@attr.s(auto_attribs=True)
class RunResults:
    """
    Attributes:
        cancelled (int):
        crashed (int):
        errored (int):
        exited (int):
        pending (int):
        running (int):
    """

    cancelled: int
    crashed: int
    errored: int
    exited: int
    pending: int
    running: int

    def to_dict(self) -> Dict[str, Any]:
        cancelled = self.cancelled
        crashed = self.crashed
        errored = self.errored
        exited = self.exited
        pending = self.pending
        running = self.running

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "cancelled": cancelled,
                "crashed": crashed,
                "errored": errored,
                "exited": exited,
                "pending": pending,
                "running": running,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        cancelled = d.pop("cancelled")

        crashed = d.pop("crashed")

        errored = d.pop("errored")

        exited = d.pop("exited")

        pending = d.pop("pending")

        running = d.pop("running")

        run_results = cls(
            cancelled=cancelled,
            crashed=crashed,
            errored=errored,
            exited=exited,
            pending=pending,
            running=running,
        )

        return run_results
