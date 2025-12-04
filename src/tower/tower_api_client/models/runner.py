from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="Runner")


@_attrs_define
class Runner:
    """
    Attributes:
        active_runs (list['Run']):
        created_at (str):
        id (str):
        max_concurrent_apps (int):
        num_runs (int):
        status (str):
        last_health_check_at (Union[Unset, str]):
    """

    active_runs: list["Run"]
    created_at: str
    id: str
    max_concurrent_apps: int
    num_runs: int
    status: str
    last_health_check_at: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        active_runs = []
        for active_runs_item_data in self.active_runs:
            active_runs_item = active_runs_item_data.to_dict()
            active_runs.append(active_runs_item)

        created_at = self.created_at

        id = self.id

        max_concurrent_apps = self.max_concurrent_apps

        num_runs = self.num_runs

        status = self.status

        last_health_check_at = self.last_health_check_at

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "active_runs": active_runs,
                "created_at": created_at,
                "id": id,
                "max_concurrent_apps": max_concurrent_apps,
                "num_runs": num_runs,
                "status": status,
            }
        )
        if last_health_check_at is not UNSET:
            field_dict["last_health_check_at"] = last_health_check_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run

        d = dict(src_dict)
        active_runs = []
        _active_runs = d.pop("active_runs")
        for active_runs_item_data in _active_runs:
            active_runs_item = Run.from_dict(active_runs_item_data)

            active_runs.append(active_runs_item)

        created_at = d.pop("created_at")

        id = d.pop("id")

        max_concurrent_apps = d.pop("max_concurrent_apps")

        num_runs = d.pop("num_runs")

        status = d.pop("status")

        last_health_check_at = d.pop("last_health_check_at", UNSET)

        runner = cls(
            active_runs=active_runs,
            created_at=created_at,
            id=id,
            max_concurrent_apps=max_concurrent_apps,
            num_runs=num_runs,
            status=status,
            last_health_check_at=last_health_check_at,
        )

        return runner
