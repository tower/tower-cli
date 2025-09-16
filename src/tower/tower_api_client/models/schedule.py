import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

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
        created_at (datetime.datetime): The timestamp when the schedule was created
        cron (str): The cron expression defining when the app should run
        environment (str): The environment to run the app in
        id (str): The unique identifier for the schedule
        status (ScheduleStatus): The status of the schedule
        updated_at (datetime.datetime): The timestamp when the schedule was last updated
        app_version (Union[Unset, str]): The specific app version to run, or null for the default version
        parameters (Union[Unset, list['RunParameter']]): The parameters to pass when running the app
    """

    app_name: str
    created_at: datetime.datetime
    cron: str
    environment: str
    id: str
    status: ScheduleStatus
    updated_at: datetime.datetime
    app_version: Union[Unset, str] = UNSET
    parameters: Union[Unset, list["RunParameter"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        app_name = self.app_name

        created_at = self.created_at.isoformat()

        cron = self.cron

        environment = self.environment

        id = self.id

        status = self.status.value

        updated_at = self.updated_at.isoformat()

        app_version = self.app_version

        parameters: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = []
            for parameters_item_data in self.parameters:
                parameters_item = parameters_item_data.to_dict()
                parameters.append(parameters_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app_name": app_name,
                "created_at": created_at,
                "cron": cron,
                "environment": environment,
                "id": id,
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

        created_at = isoparse(d.pop("created_at"))

        cron = d.pop("cron")

        environment = d.pop("environment")

        id = d.pop("id")

        status = ScheduleStatus(d.pop("status"))

        updated_at = isoparse(d.pop("updated_at"))

        app_version = d.pop("app_version", UNSET)

        parameters = []
        _parameters = d.pop("parameters", UNSET)
        for parameters_item_data in _parameters or []:
            parameters_item = RunParameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        schedule = cls(
            app_name=app_name,
            created_at=created_at,
            cron=cron,
            environment=environment,
            id=id,
            status=status,
            updated_at=updated_at,
            app_version=app_version,
            parameters=parameters,
        )

        return schedule
