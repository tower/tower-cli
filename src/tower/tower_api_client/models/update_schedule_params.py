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
        name (None | str): The name for this schedule. Must be unique per team.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateScheduleParams.json.
        app_version (None | str | Unset): The specific app version to run (if omitted, will use the app's default
            version)
        cron (str | Unset): The cron expression defining when the app should run
        environment (str | Unset): The environment to run the app in Default: 'default'.
        overlap_policy (UpdateScheduleParamsOverlapPolicy | Unset): The overlap policy for the schedule
        parameters (list[RunParameter] | Unset): Parameters to pass when running the app
        status (UpdateScheduleParamsStatus | Unset): The status of the schedule
    """

    name: None | str
    schema: str | Unset = UNSET
    app_version: None | str | Unset = UNSET
    cron: str | Unset = UNSET
    environment: str | Unset = "default"
    overlap_policy: UpdateScheduleParamsOverlapPolicy | Unset = UNSET
    parameters: list[RunParameter] | Unset = UNSET
    status: UpdateScheduleParamsStatus | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str
        name = self.name

        schema = self.schema

        app_version: None | str | Unset
        if isinstance(self.app_version, Unset):
            app_version = UNSET
        else:
            app_version = self.app_version

        cron = self.cron

        environment = self.environment

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

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if app_version is not UNSET:
            field_dict["app_version"] = app_version
        if cron is not UNSET:
            field_dict["cron"] = cron
        if environment is not UNSET:
            field_dict["environment"] = environment
        if overlap_policy is not UNSET:
            field_dict["overlap_policy"] = overlap_policy
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_parameter import RunParameter

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

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

        update_schedule_params = cls(
            name=name,
            schema=schema,
            app_version=app_version,
            cron=cron,
            environment=environment,
            overlap_policy=overlap_policy,
            parameters=parameters,
            status=status,
        )

        return update_schedule_params
