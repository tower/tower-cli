from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule import Schedule


T = TypeVar("T", bound="UpdateScheduleResponse")


@_attrs_define
class UpdateScheduleResponse:
    """
    Attributes:
        schedule (Schedule):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateScheduleResponse.json.
    """

    schedule: "Schedule"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schedule = self.schedule.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "schedule": schedule,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule import Schedule

        d = dict(src_dict)
        schedule = Schedule.from_dict(d.pop("schedule"))

        schema = d.pop("$schema", UNSET)

        update_schedule_response = cls(
            schedule=schedule,
            schema=schema,
        )

        return update_schedule_response
