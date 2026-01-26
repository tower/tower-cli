from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ScheduleRunInitiatorDetails")


@_attrs_define
class ScheduleRunInitiatorDetails:
    """
    Attributes:
        schedule_name (str | Unset): The name of the schedule that initiated this run, if type is 'tower_schedule'
    """

    schedule_name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schedule_name = self.schedule_name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schedule_name is not UNSET:
            field_dict["schedule_name"] = schedule_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schedule_name = d.pop("schedule_name", UNSET)

        schedule_run_initiator_details = cls(
            schedule_name=schedule_name,
        )

        return schedule_run_initiator_details
