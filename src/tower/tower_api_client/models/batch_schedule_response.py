from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule import Schedule


T = TypeVar("T", bound="BatchScheduleResponse")


@_attrs_define
class BatchScheduleResponse:
    """
    Attributes:
        schedules (list['Schedule']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/BatchScheduleResponse.json.
    """

    schedules: list["Schedule"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schedules = []
        for schedules_item_data in self.schedules:
            schedules_item = schedules_item_data.to_dict()
            schedules.append(schedules_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "schedules": schedules,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule import Schedule

        d = dict(src_dict)
        schedules = []
        _schedules = d.pop("schedules")
        for schedules_item_data in _schedules:
            schedules_item = Schedule.from_dict(schedules_item_data)

            schedules.append(schedules_item)

        schema = d.pop("$schema", UNSET)

        batch_schedule_response = cls(
            schedules=schedules,
            schema=schema,
        )

        return batch_schedule_response
