from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.plan import Plan


T = TypeVar("T", bound="UpdatePlanResponse")


@_attrs_define
class UpdatePlanResponse:
    """
    Attributes:
        plan (Plan):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdatePlanResponse.json.
    """

    plan: "Plan"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        plan = self.plan.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "plan": plan,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.plan import Plan

        d = dict(src_dict)
        plan = Plan.from_dict(d.pop("plan"))

        schema = d.pop("$schema", UNSET)

        update_plan_response = cls(
            plan=plan,
            schema=schema,
        )

        return update_plan_response
