from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePlanParams")


@_attrs_define
class UpdatePlanParams:
    """
    Attributes:
        base_plan_name (str): The name of the base plan to use.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdatePlanParams.json.
    """

    base_plan_name: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        base_plan_name = self.base_plan_name

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "base_plan_name": base_plan_name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        base_plan_name = d.pop("base_plan_name")

        schema = d.pop("$schema", UNSET)

        update_plan_params = cls(
            base_plan_name=base_plan_name,
            schema=schema,
        )

        return update_plan_params
