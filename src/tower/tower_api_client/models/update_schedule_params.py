from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.update_schedule_params_overlap_policy import (
    UpdateScheduleParamsOverlapPolicy,
)
from ..models.update_schedule_params_status import UpdateScheduleParamsStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_parameter import RunParameter


T = TypeVar("T", bound="UpdateScheduleParams")


@_attrs_define
class UpdateScheduleParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateScheduleParams.json.
        app_version (None | str | Unset): The specific app version to run (if omitted, will use the app's default
            version)
        cron (str | Unset): The cron expression defining when the app should run
        environment (str | Unset): The environment to run the app in Default: 'default'.
        name (None | str | Unset): The name for this schedule. Must be unique per team.
        overlap_policy (UpdateScheduleParamsOverlapPolicy | Unset): The overlap policy for the schedule
        parameters (list[RunParameter] | Unset): Parameters to pass when running the app
        status (UpdateScheduleParamsStatus | Unset): The status of the schedule
        timezone (None | str | Unset): The IANA timezone identifier that the cron expression should be evaluated in
            (e.g., 'America/New_York', 'Europe/London').
    """

    schema: str | Unset = UNSET
    app_version: None | str | Unset = UNSET
    cron: str | Unset = UNSET
    environment: str | Unset = "default"
    name: None | str | Unset = UNSET
    overlap_policy: UpdateScheduleParamsOverlapPolicy | Unset = UNSET
    parameters: list[RunParameter] | Unset = UNSET
    status: UpdateScheduleParamsStatus | Unset = UNSET
    timezone: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        app_version: None | str | Unset
        if isinstance(self.app_version, Unset):
            app_version = UNSET
        else:
            app_version = self.app_version

        cron = self.cron

        environment = self.environment

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        overlap_policy: str | Unset = UNSET
        if not isinstance(self.overlap_policy, Unset):
            overlap_policy = self.overlap_policy.value

        parameters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        timezone: None | str | Unset
        if isinstance(self.timezone, Unset):
            timezone = UNSET
        else:
            timezone = self.timezone

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if app_version is not UNSET:
            field_dict["app_version"] = app_version
        if cron is not UNSET:
            field_dict["cron"] = cron
        if environment is not UNSET:
            field_dict["environment"] = environment
        if name is not UNSET:
            field_dict["name"] = name
        if overlap_policy is not UNSET:
            field_dict["overlap_policy"] = overlap_policy
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if status is not UNSET:
            field_dict["status"] = status
        if timezone is not UNSET:
            field_dict["timezone"] = timezone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_parameter import RunParameter

        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        def _parse_app_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_version = _parse_app_version(d.pop("app_version", UNSET))

        cron = d.pop("cron", UNSET)

        environment = d.pop("environment", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        _overlap_policy = d.pop("overlap_policy", UNSET)
        overlap_policy: UpdateScheduleParamsOverlapPolicy | Unset
        if isinstance(_overlap_policy, Unset):
            overlap_policy = UNSET
        else:
            overlap_policy = UpdateScheduleParamsOverlapPolicy(_overlap_policy)

        _parameters = d.pop("parameters", UNSET)
        parameters: list[RunParameter] | Unset = UNSET
        if _parameters is not UNSET:
            parameters = []
            for parameters_item_data in _parameters:
                parameters_item = RunParameter.from_dict(parameters_item_data)

                parameters.append(parameters_item)

        _status = d.pop("status", UNSET)
        status: UpdateScheduleParamsStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateScheduleParamsStatus(_status)

        def _parse_timezone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        timezone = _parse_timezone(d.pop("timezone", UNSET))

        update_schedule_params = cls(
            schema=schema,
            app_version=app_version,
            cron=cron,
            environment=environment,
            name=name,
            overlap_policy=overlap_policy,
            parameters=parameters,
            status=status,
            timezone=timezone,
        )

        return update_schedule_params
