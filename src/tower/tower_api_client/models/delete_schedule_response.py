from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteScheduleResponse")


@_attrs_define
class DeleteScheduleResponse:
    """
    Attributes:
        id (str): The ID of the deleted schedule.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteScheduleResponse.json.
    """

    id: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "id": id,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        schema = d.pop("$schema", UNSET)

        delete_schedule_response = cls(
            id=id,
            schema=schema,
        )

        return delete_schedule_response
