from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.update_schedule_params_status import UpdateScheduleParamsStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_parameter import RunParameter


T = TypeVar("T", bound="UpdateScheduleParams")


@_attrs_define
class UpdateScheduleParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateScheduleParams.json.
        app_version (Union[None, Unset, str]): The specific app version to run (if omitted, will use the app's default
            version)
        cron (Union[Unset, str]): The cron expression defining when the app should run
        environment (Union[Unset, str]): The environment to run the app in
        parameters (Union[Unset, list['RunParameter']]): Parameters to pass when running the app
        status (Union[Unset, UpdateScheduleParamsStatus]): The status of the schedule
    """

    schema: Union[Unset, str] = UNSET
    app_version: Union[None, Unset, str] = UNSET
    cron: Union[Unset, str] = UNSET
    environment: Union[Unset, str] = UNSET
    parameters: Union[Unset, list["RunParameter"]] = UNSET
    status: Union[Unset, UpdateScheduleParamsStatus] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        app_version: Union[None, Unset, str]
        if isinstance(self.app_version, Unset):
            app_version = UNSET
        else:
            app_version = self.app_version

        cron = self.cron

        environment = self.environment

        parameters: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

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
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_parameter import RunParameter

        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        def _parse_app_version(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        app_version = _parse_app_version(d.pop("app_version", UNSET))

        cron = d.pop("cron", UNSET)

        environment = d.pop("environment", UNSET)

        parameters = []
        _parameters = d.pop("parameters", UNSET)
        for parameters_item_data in _parameters or []:
            parameters_item = RunParameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        _status = d.pop("status", UNSET)
        status: Union[Unset, UpdateScheduleParamsStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateScheduleParamsStatus(_status)

        update_schedule_params = cls(
            schema=schema,
            app_version=app_version,
            cron=cron,
            environment=environment,
            parameters=parameters,
            status=status,
        )

        return update_schedule_params
