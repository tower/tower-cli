from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.usage_limit import UsageLimit


T = TypeVar("T", bound="OrganizationUsage")


@_attrs_define
class OrganizationUsage:
    """
    Attributes:
        active_schedules (UsageLimit):
        apps (UsageLimit):
        base_plan_name (str): The name of the organization's base plan.
        compute_minutes (UsageLimit):
        members (UsageLimit):
        organization_name (str): The name of the organization.
        self_hosted_runners (UsageLimit):
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/OrganizationUsage.json.
    """

    active_schedules: UsageLimit
    apps: UsageLimit
    base_plan_name: str
    compute_minutes: UsageLimit
    members: UsageLimit
    organization_name: str
    self_hosted_runners: UsageLimit
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        active_schedules = self.active_schedules.to_dict()

        apps = self.apps.to_dict()

        base_plan_name = self.base_plan_name

        compute_minutes = self.compute_minutes.to_dict()

        members = self.members.to_dict()

        organization_name = self.organization_name

        self_hosted_runners = self.self_hosted_runners.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "active_schedules": active_schedules,
                "apps": apps,
                "base_plan_name": base_plan_name,
                "compute_minutes": compute_minutes,
                "members": members,
                "organization_name": organization_name,
                "self_hosted_runners": self_hosted_runners,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_limit import UsageLimit

        d = dict(src_dict)
        active_schedules = UsageLimit.from_dict(d.pop("active_schedules"))

        apps = UsageLimit.from_dict(d.pop("apps"))

        base_plan_name = d.pop("base_plan_name")

        compute_minutes = UsageLimit.from_dict(d.pop("compute_minutes"))

        members = UsageLimit.from_dict(d.pop("members"))

        organization_name = d.pop("organization_name")

        self_hosted_runners = UsageLimit.from_dict(d.pop("self_hosted_runners"))

        schema = d.pop("$schema", UNSET)

        organization_usage = cls(
            active_schedules=active_schedules,
            apps=apps,
            base_plan_name=base_plan_name,
            compute_minutes=compute_minutes,
            members=members,
            organization_name=organization_name,
            self_hosted_runners=self_hosted_runners,
            schema=schema,
        )

        return organization_usage
