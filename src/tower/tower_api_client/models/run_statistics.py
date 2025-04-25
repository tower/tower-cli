from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunStatistics")


@_attrs_define
class RunStatistics:
    """
    Attributes:
        failed_runs (int):
        successful_runs (int):
        total_runs (int):
    """

    failed_runs: int
    successful_runs: int
    total_runs: int

    def to_dict(self) -> dict[str, Any]:
        failed_runs = self.failed_runs

        successful_runs = self.successful_runs

        total_runs = self.total_runs

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "failed_runs": failed_runs,
                "successful_runs": successful_runs,
                "total_runs": total_runs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        failed_runs = d.pop("failed_runs")

        successful_runs = d.pop("successful_runs")

        total_runs = d.pop("total_runs")

        run_statistics = cls(
            failed_runs=failed_runs,
            successful_runs=successful_runs,
            total_runs=total_runs,
        )

        return run_statistics
