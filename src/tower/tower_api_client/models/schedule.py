from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.schedule_app_status import ScheduleAppStatus
from ..models.schedule_overlap_policy import ScheduleOverlapPolicy
from ..models.schedule_status import ScheduleStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_parameter import RunParameter


T = TypeVar("T", bound="Schedule")


@_attrs_define
class Schedule:
    """
    Attributes:
        app_name (str): The name of the app that will be executed
        app_status (ScheduleAppStatus): The status of the app
        created_at (datetime.datetime): The timestamp when the schedule was created
        cron (str): The cron expression defining when the app should run
        environment (str): The environment to run the app in
        id (str): The unique identifier for the schedule
        name (str): The name of this schedule
        overlap_policy (ScheduleOverlapPolicy): The policy for handling overlapping runs
        status (ScheduleStatus): The status of the schedule
        updated_at (datetime.datetime): The timestamp when the schedule was last updated
        app_version (str | Unset): The specific app version to run, or null for the default version
        parameters (list[RunParameter] | Unset): The parameters to pass when running the app
    """

    app_name: str
    app_status: ScheduleAppStatus
    created_at: datetime.datetime
    cron: str
    environment: str
    id: str
    name: str
    overlap_policy: ScheduleOverlapPolicy
    status: ScheduleStatus
    updated_at: datetime.datetime
    app_version: str | Unset = UNSET
    parameters: list[RunParameter] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        app_name = self.app_name

        app_status = self.app_status.value

        created_at = self.created_at.isoformat()

        cron = self.cron

        environment = self.environment

        id = self.id

        name = self.name

        overlap_policy = self.overlap_policy.value

        status = self.status.value

        updated_at = self.updated_at.isoformat()

        app_version = self.app_version

        parameters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "app_name": app_name,
                "app_status": app_status,
                "created_at": created_at,
                "cron": cron,
                "environment": environment,
                "id": id,
                "name": name,
                "overlap_policy": overlap_policy,
                "status": status,
                "updated_at": updated_at,
            }
        )
        if app_version is not UNSET:
            field_dict["app_version"] = app_version
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_parameter import RunParameter

        d = dict(src_dict)
        app_name = d.pop("app_name")

        app_status = ScheduleAppStatus(d.pop("app_status"))

        created_at = isoparse(d.pop("created_at"))

        cron = d.pop("cron")

        environment = d.pop("environment")

        id = d.pop("id")

        name = d.pop("name")

        overlap_policy = ScheduleOverlapPolicy(d.pop("overlap_policy"))

        status = ScheduleStatus(d.pop("status"))

        updated_at = isoparse(d.pop("updated_at"))

        app_version = d.pop("app_version", UNSET)

        _parameters = d.pop("parameters", UNSET)
        parameters: list[RunParameter] | Unset = UNSET
        if _parameters is not UNSET:
            parameters = []
            for parameters_item_data in _parameters:
                parameters_item = RunParameter.from_dict(parameters_item_data)

                parameters.append(parameters_item)

        schedule = cls(
            app_name=app_name,
            app_status=app_status,
            created_at=created_at,
            cron=cron,
            environment=environment,
            id=id,
            name=name,
            overlap_policy=overlap_policy,
            status=status,
            updated_at=updated_at,
            app_version=app_version,
            parameters=parameters,
        )

        return schedule
