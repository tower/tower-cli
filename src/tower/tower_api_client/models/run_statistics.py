from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunStatistics")


@_attrs_define
class RunStatistics:
    """
    Attributes:
        cancelled_runs (int):
        crashed_runs (int):
        errored_runs (int):
        exited_runs (int):
        running_runs (int):
        total_runs (int):
    """

    cancelled_runs: int
    crashed_runs: int
    errored_runs: int
    exited_runs: int
    running_runs: int
    total_runs: int

    def to_dict(self) -> dict[str, Any]:
        cancelled_runs = self.cancelled_runs

        crashed_runs = self.crashed_runs

        errored_runs = self.errored_runs

        exited_runs = self.exited_runs

        running_runs = self.running_runs

        total_runs = self.total_runs

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "cancelled_runs": cancelled_runs,
                "crashed_runs": crashed_runs,
                "errored_runs": errored_runs,
                "exited_runs": exited_runs,
                "running_runs": running_runs,
                "total_runs": total_runs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cancelled_runs = d.pop("cancelled_runs")

        crashed_runs = d.pop("crashed_runs")

        errored_runs = d.pop("errored_runs")

        exited_runs = d.pop("exited_runs")

        running_runs = d.pop("running_runs")

        total_runs = d.pop("total_runs")

        run_statistics = cls(
            cancelled_runs=cancelled_runs,
            crashed_runs=crashed_runs,
            errored_runs=errored_runs,
            exited_runs=exited_runs,
            running_runs=running_runs,
            total_runs=total_runs,
        )

        return run_statistics
