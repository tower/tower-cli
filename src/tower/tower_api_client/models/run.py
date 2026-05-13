from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.run_status import RunStatus
from ..models.run_status_group import RunStatusGroup
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_attempt import RunAttempt
    from ..models.run_initiator import RunInitiator
    from ..models.run_parameter import RunParameter
    from ..models.run_retry_policy import RunRetryPolicy


T = TypeVar("T", bound="Run")


@_attrs_define
class Run:
    """
    Attributes:
        link (str): $link is deprecated. Individual responses include links.
        app_name (str):
        app_version (str):
        cancelled_at (datetime.datetime | None):
        created_at (datetime.datetime):
        ended_at (datetime.datetime | None):
        environment (str):
        exit_code (int | None): Exit code of the run, if the run is completed. Null if there is no exit code
        initiator (RunInitiator):
        is_scheduled (bool): Whether this run was triggered by a schedule (true) or on-demand (false). Historical
            records default to false.
        num_attempts (int): Number of attempts for this run (1 = original, 2+ = retries).
        number (int):
        parameters (list[RunParameter]): Parameters used to invoke this run.
        run_id (str):
        scheduled_at (datetime.datetime):
        started_at (datetime.datetime | None): When the run started executing your code.
        starting_at (datetime.datetime | None): When the runner environment started to get setup.
        status (RunStatus):
        status_group (RunStatusGroup):
        app_slug (str | Unset): This property is deprecated. Use app_name instead.
        attempts (list[RunAttempt] | Unset): Previous attempt details. Populated on describe, omitted on list.
        hostname (str | Unset): hostname is deprecated, use subdomain
        retry_policy (RunRetryPolicy | Unset):
        subdomain (None | str | Unset): If app is externally accessible, then you can access this run with this
            hostname.
    """

    link: str
    app_name: str
    app_version: str
    cancelled_at: datetime.datetime | None
    created_at: datetime.datetime
    ended_at: datetime.datetime | None
    environment: str
    exit_code: int | None
    initiator: RunInitiator
    is_scheduled: bool
    num_attempts: int
    number: int
    parameters: list[RunParameter]
    run_id: str
    scheduled_at: datetime.datetime
    started_at: datetime.datetime | None
    starting_at: datetime.datetime | None
    status: RunStatus
    status_group: RunStatusGroup
    app_slug: str | Unset = UNSET
    attempts: list[RunAttempt] | Unset = UNSET
    hostname: str | Unset = UNSET
    retry_policy: RunRetryPolicy | Unset = UNSET
    subdomain: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        link = self.link

        app_name = self.app_name

        app_version = self.app_version

        cancelled_at: None | str
        if isinstance(self.cancelled_at, datetime.datetime):
            cancelled_at = self.cancelled_at.isoformat()
        else:
            cancelled_at = self.cancelled_at

        created_at = self.created_at.isoformat()

        ended_at: None | str
        if isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        environment = self.environment

        exit_code: int | None
        exit_code = self.exit_code

        initiator = self.initiator.to_dict()

        is_scheduled = self.is_scheduled

        num_attempts = self.num_attempts

        number = self.number

        parameters = []
        for parameters_item_data in self.parameters:
            parameters_item = parameters_item_data.to_dict()
            parameters.append(parameters_item)

        run_id = self.run_id

        scheduled_at = self.scheduled_at.isoformat()

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        starting_at: None | str
        if isinstance(self.starting_at, datetime.datetime):
            starting_at = self.starting_at.isoformat()
        else:
            starting_at = self.starting_at

        status = self.status.value

        status_group = self.status_group.value

        app_slug = self.app_slug

        attempts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.attempts, Unset):
            attempts = []
            for attempts_item_data in self.attempts:
                attempts_item = attempts_item_data.to_dict()
                attempts.append(attempts_item)

        hostname = self.hostname

        retry_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retry_policy, Unset):
            retry_policy = self.retry_policy.to_dict()

        subdomain: None | str | Unset
        if isinstance(self.subdomain, Unset):
            subdomain = UNSET
        else:
            subdomain = self.subdomain

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
                "initiator": initiator,
                "is_scheduled": is_scheduled,
                "num_attempts": num_attempts,
                "number": number,
                "parameters": parameters,
                "run_id": run_id,
                "scheduled_at": scheduled_at,
                "started_at": started_at,
                "starting_at": starting_at,
                "status": status,
                "status_group": status_group,
            }
        )
        if app_slug is not UNSET:
            field_dict["app_slug"] = app_slug
        if attempts is not UNSET:
            field_dict["attempts"] = attempts
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if retry_policy is not UNSET:
            field_dict["retry_policy"] = retry_policy
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_attempt import RunAttempt
        from ..models.run_initiator import RunInitiator
        from ..models.run_parameter import RunParameter
        from ..models.run_retry_policy import RunRetryPolicy

        d = dict(src_dict)
        link = d.pop("$link")

        app_name = d.pop("app_name")

        app_version = d.pop("app_version")

        def _parse_cancelled_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                cancelled_at_type_0 = isoparse(data)

                return cancelled_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        cancelled_at = _parse_cancelled_at(d.pop("cancelled_at"))

        created_at = isoparse(d.pop("created_at"))

        def _parse_ended_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = isoparse(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        ended_at = _parse_ended_at(d.pop("ended_at"))

        environment = d.pop("environment")

        def _parse_exit_code(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        exit_code = _parse_exit_code(d.pop("exit_code"))

        initiator = RunInitiator.from_dict(d.pop("initiator"))

        is_scheduled = d.pop("is_scheduled")

        num_attempts = d.pop("num_attempts")

        number = d.pop("number")

        parameters = []
        _parameters = d.pop("parameters")
        for parameters_item_data in _parameters:
            parameters_item = RunParameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        run_id = d.pop("run_id")

        scheduled_at = isoparse(d.pop("scheduled_at"))

        def _parse_started_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        started_at = _parse_started_at(d.pop("started_at"))

        def _parse_starting_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                starting_at_type_0 = isoparse(data)

                return starting_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        starting_at = _parse_starting_at(d.pop("starting_at"))

        status = RunStatus(d.pop("status"))

        status_group = RunStatusGroup(d.pop("status_group"))

        app_slug = d.pop("app_slug", UNSET)

        _attempts = d.pop("attempts", UNSET)
        attempts: list[RunAttempt] | Unset = UNSET
        if _attempts is not UNSET:
            attempts = []
            for attempts_item_data in _attempts:
                attempts_item = RunAttempt.from_dict(attempts_item_data)

                attempts.append(attempts_item)

        hostname = d.pop("hostname", UNSET)

        _retry_policy = d.pop("retry_policy", UNSET)
        retry_policy: RunRetryPolicy | Unset
        if isinstance(_retry_policy, Unset):
            retry_policy = UNSET
        else:
            retry_policy = RunRetryPolicy.from_dict(_retry_policy)

        def _parse_subdomain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subdomain = _parse_subdomain(d.pop("subdomain", UNSET))

        run = cls(
            link=link,
            app_name=app_name,
            app_version=app_version,
            cancelled_at=cancelled_at,
            created_at=created_at,
            ended_at=ended_at,
            environment=environment,
            exit_code=exit_code,
            initiator=initiator,
            is_scheduled=is_scheduled,
            num_attempts=num_attempts,
            number=number,
            parameters=parameters,
            run_id=run_id,
            scheduled_at=scheduled_at,
            started_at=started_at,
            starting_at=starting_at,
            status=status,
            status_group=status_group,
            app_slug=app_slug,
            attempts=attempts,
            hostname=hostname,
            retry_policy=retry_policy,
            subdomain=subdomain,
        )

        return run
