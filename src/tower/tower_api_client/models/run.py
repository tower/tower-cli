import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.run_status import RunStatus
from ..models.run_status_group import RunStatusGroup
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_parameter import RunParameter


T = TypeVar("T", bound="Run")


@_attrs_define
class Run:
    """
    Attributes:
        link (str): Link to the run in the Tower UI
        app_name (str):
        app_version (str):
        cancelled_at (Union[None, datetime.datetime]):
        created_at (datetime.datetime):
        ended_at (Union[None, datetime.datetime]):
        environment (str):
        exit_code (Union[None, int]): Exit code of the run, if the run is completed. Null if there is no exit code
        number (int):
        parameters (list['RunParameter']): Parameters used to invoke this run.
        run_id (str):
        scheduled_at (datetime.datetime):
        started_at (Union[None, datetime.datetime]):
        status (RunStatus):
        status_group (RunStatusGroup):
        app_slug (Union[Unset, str]): This property is deprecated. Please use app_name instead.
        hostname (Union[Unset, str]): If app is externally accessible, then you can access this run with this hostname
    """

    link: str
    app_name: str
    app_version: str
    cancelled_at: Union[None, datetime.datetime]
    created_at: datetime.datetime
    ended_at: Union[None, datetime.datetime]
    environment: str
    exit_code: Union[None, int]
    number: int
    parameters: list["RunParameter"]
    run_id: str
    scheduled_at: datetime.datetime
    started_at: Union[None, datetime.datetime]
    status: RunStatus
    status_group: RunStatusGroup
    app_slug: Union[Unset, str] = UNSET
    hostname: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        link = self.link

        app_name = self.app_name

        app_version = self.app_version

        cancelled_at: Union[None, str]
        if isinstance(self.cancelled_at, datetime.datetime):
            cancelled_at = self.cancelled_at.isoformat()
        else:
            cancelled_at = self.cancelled_at

        created_at = self.created_at.isoformat()

        ended_at: Union[None, str]
        if isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        environment = self.environment

        exit_code: Union[None, int]
        exit_code = self.exit_code

        number = self.number

        parameters = []
        for parameters_item_data in self.parameters:
            parameters_item = parameters_item_data.to_dict()
            parameters.append(parameters_item)

        run_id = self.run_id

        scheduled_at = self.scheduled_at.isoformat()

        started_at: Union[None, str]
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status.value

        status_group = self.status_group.value

        app_slug = self.app_slug

        hostname = self.hostname

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "$link": link,
                "app_name": app_name,
                "app_version": app_version,
                "cancelled_at": cancelled_at,
                "created_at": created_at,
                "ended_at": ended_at,
                "environment": environment,
                "exit_code": exit_code,
                "number": number,
                "parameters": parameters,
                "run_id": run_id,
                "scheduled_at": scheduled_at,
                "started_at": started_at,
                "status": status,
                "status_group": status_group,
            }
        )
        if app_slug is not UNSET:
            field_dict["app_slug"] = app_slug
        if hostname is not UNSET:
            field_dict["hostname"] = hostname

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_parameter import RunParameter

        d = dict(src_dict)
        link = d.pop("$link")

        app_name = d.pop("app_name")

        app_version = d.pop("app_version")

        def _parse_cancelled_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                cancelled_at_type_0 = isoparse(data)

                return cancelled_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        cancelled_at = _parse_cancelled_at(d.pop("cancelled_at"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_ended_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        ended_at = _parse_ended_at(d.pop("ended_at"))

        environment = d.pop("environment")

        def _parse_exit_code(data: object) -> Union[None, int]:
            if data is None:
                return data
            return cast(Union[None, int], data)

        exit_code = _parse_exit_code(d.pop("exit_code"))

        number = d.pop("number")

        parameters = []
        _parameters = d.pop("parameters")
        for parameters_item_data in _parameters:
            parameters_item = RunParameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        run_id = d.pop("run_id")

        scheduled_at = isoparse(d.pop("scheduled_at"))

        def _parse_started_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        started_at = _parse_started_at(d.pop("started_at"))

        status = RunStatus(d.pop("status"))

        status_group = RunStatusGroup(d.pop("status_group"))

        app_slug = d.pop("app_slug", UNSET)

        hostname = d.pop("hostname", UNSET)

        run = cls(
            link=link,
            app_name=app_name,
            app_version=app_version,
            cancelled_at=cancelled_at,
            created_at=created_at,
            ended_at=ended_at,
            environment=environment,
            exit_code=exit_code,
            number=number,
            parameters=parameters,
            run_id=run_id,
            scheduled_at=scheduled_at,
            started_at=started_at,
            status=status,
            status_group=status_group,
            app_slug=app_slug,
            hostname=hostname,
        )

        return run
