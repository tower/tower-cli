from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteScheduleParams")


@_attrs_define
class DeleteScheduleParams:
    """
    Attributes:
        ids (list[str]): The IDs of the schedules to delete.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteScheduleParams.json.
    """

    ids: list[str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        ids = self.ids

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "ids": ids,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ids = cast(list[str], d.pop("ids"))

        schema = d.pop("$schema", UNSET)

        delete_schedule_params = cls(
            ids=ids,
            schema=schema,
        )

        return delete_schedule_params
