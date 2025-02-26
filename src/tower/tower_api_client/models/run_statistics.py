from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="RunStatistics")


@attr.s(auto_attribs=True)
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

    def to_dict(self) -> Dict[str, Any]:
        failed_runs = self.failed_runs
        successful_runs = self.successful_runs
        total_runs = self.total_runs

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "failed_runs": failed_runs,
                "successful_runs": successful_runs,
                "total_runs": total_runs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        failed_runs = d.pop("failed_runs")

        successful_runs = d.pop("successful_runs")

        total_runs = d.pop("total_runs")

        run_statistics = cls(
            failed_runs=failed_runs,
            successful_runs=successful_runs,
            total_runs=total_runs,
        )

        return run_statistics
