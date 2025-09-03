from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule import Schedule


T = TypeVar("T", bound="DeleteScheduleResponse")


@_attrs_define
class DeleteScheduleResponse:
    """
    Attributes:
        the_schedules_successfully_deleted (list['Schedule']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteScheduleResponse.json.
    """

    the_schedules_successfully_deleted: list["Schedule"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        the_schedules_successfully_deleted = []
        for (
            the_schedules_successfully_deleted_item_data
        ) in self.the_schedules_successfully_deleted:
            the_schedules_successfully_deleted_item = (
                the_schedules_successfully_deleted_item_data.to_dict()
            )
            the_schedules_successfully_deleted.append(
                the_schedules_successfully_deleted_item
            )

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "the schedules successfully deleted": the_schedules_successfully_deleted,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule import Schedule

        d = dict(src_dict)
        the_schedules_successfully_deleted = []
        _the_schedules_successfully_deleted = d.pop(
            "the schedules successfully deleted"
        )
        for (
            the_schedules_successfully_deleted_item_data
        ) in _the_schedules_successfully_deleted:
            the_schedules_successfully_deleted_item = Schedule.from_dict(
                the_schedules_successfully_deleted_item_data
            )

            the_schedules_successfully_deleted.append(
                the_schedules_successfully_deleted_item
            )

        schema = d.pop("$schema", UNSET)

        delete_schedule_response = cls(
            the_schedules_successfully_deleted=the_schedules_successfully_deleted,
            schema=schema,
        )

        return delete_schedule_response
