from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Features")


@_attrs_define
class Features:
    """
    Attributes:
        has_self_hosted_runners (Union[Unset, bool]): Whether self-hosted runners are enabled
        num_apps (Union[Unset, int]): The number of apps that can be created
        num_minutes (Union[Unset, int]): The number of minutes that can be used for free per month
        num_schedules (Union[Unset, int]): The number of schedules that can be created
        num_team_members (Union[Unset, int]): The number of team members that can be added
    """

    has_self_hosted_runners: Union[Unset, bool] = UNSET
    num_apps: Union[Unset, int] = UNSET
    num_minutes: Union[Unset, int] = UNSET
    num_schedules: Union[Unset, int] = UNSET
    num_team_members: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        has_self_hosted_runners = self.has_self_hosted_runners

        num_apps = self.num_apps

        num_minutes = self.num_minutes

        num_schedules = self.num_schedules

        num_team_members = self.num_team_members

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if has_self_hosted_runners is not UNSET:
            field_dict["has_self_hosted_runners"] = has_self_hosted_runners
        if num_apps is not UNSET:
            field_dict["num_apps"] = num_apps
        if num_minutes is not UNSET:
            field_dict["num_minutes"] = num_minutes
        if num_schedules is not UNSET:
            field_dict["num_schedules"] = num_schedules
        if num_team_members is not UNSET:
            field_dict["num_team_members"] = num_team_members

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        has_self_hosted_runners = d.pop("has_self_hosted_runners", UNSET)

        num_apps = d.pop("num_apps", UNSET)

        num_minutes = d.pop("num_minutes", UNSET)

        num_schedules = d.pop("num_schedules", UNSET)

        num_team_members = d.pop("num_team_members", UNSET)

        features = cls(
            has_self_hosted_runners=has_self_hosted_runners,
            num_apps=num_apps,
            num_minutes=num_minutes,
            num_schedules=num_schedules,
            num_team_members=num_team_members,
        )

        return features
