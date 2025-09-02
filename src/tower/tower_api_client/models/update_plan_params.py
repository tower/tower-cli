import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePlanParams")


@_attrs_define
class UpdatePlanParams:
    """
    Attributes:
        base_plan_name (str): The name of the base plan to use.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdatePlanParams.json.
        end_at (Union[Unset, datetime.datetime]): Optional expiration date for the plan.
    """

    base_plan_name: str
    schema: Union[Unset, str] = UNSET
    end_at: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        base_plan_name = self.base_plan_name

        schema = self.schema

        end_at: Union[Unset, str] = UNSET
        if not isinstance(self.end_at, Unset):
            end_at = self.end_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "base_plan_name": base_plan_name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if end_at is not UNSET:
            field_dict["end_at"] = end_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        base_plan_name = d.pop("base_plan_name")

        schema = d.pop("$schema", UNSET)

        _end_at = d.pop("end_at", UNSET)
        end_at: Union[Unset, datetime.datetime]
        if isinstance(_end_at, Unset):
            end_at = UNSET
        else:
            end_at = isoparse(_end_at)

        update_plan_params = cls(
            base_plan_name=base_plan_name,
            schema=schema,
            end_at=end_at,
        )

        return update_plan_params
