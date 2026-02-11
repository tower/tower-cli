from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.app_health_status import AppHealthStatus
from ..models.app_status import AppStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run
    from ..models.run_results import RunResults


T = TypeVar("T", bound="App")


@_attrs_define
class App:
    """
    Attributes:
        created_at (datetime.datetime): The date and time this app was created.
        health_status (AppHealthStatus): This property is deprecated. It will always be 'healthy'.
        is_externally_accessible (bool):
        name (str): The name of the app.
        next_run_at (datetime.datetime | None): The next time this app will run as part of it's schedule, null if none.
        owner (str): The account slug that owns this app.
        pending_timeout (int): The maximum time in seconds that a run can stay in the pending state before being marked
            as cancelled. Default: 600.
        running_timeout (int): The number of seconds that a run can stay running before it gets cancelled. Value of 0
            (default) means no timeout. Default: 0.
        schedule (None | str): The schedule associated with this app, null if none.
        short_description (str): A short description of the app. Can be empty.
        version (None | str): The current version of this app, null if none.
        last_run (Run | Unset):
        run_results (RunResults | Unset):
        slug (str | Unset): This property is deprecated. Use name instead.
        status (AppStatus | Unset): The status of the app.
        subdomain (str | Unset): The subdomain that this app is accessible via. Must be externally accessible first.
    """

    created_at: datetime.datetime
    health_status: AppHealthStatus
    is_externally_accessible: bool
    name: str
    next_run_at: datetime.datetime | None
    owner: str
    schedule: None | str
    short_description: str
    version: None | str
    pending_timeout: int = 600
    running_timeout: int = 0
    last_run: Run | Unset = UNSET
    run_results: RunResults | Unset = UNSET
    slug: str | Unset = UNSET
    status: AppStatus | Unset = UNSET
    subdomain: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        health_status = self.health_status.value

        is_externally_accessible = self.is_externally_accessible

        name = self.name

        next_run_at: None | str
        if isinstance(self.next_run_at, datetime.datetime):
            next_run_at = self.next_run_at.isoformat()
        else:
            next_run_at = self.next_run_at

        owner = self.owner

        pending_timeout = self.pending_timeout

        running_timeout = self.running_timeout

        schedule: None | str
        schedule = self.schedule

        short_description = self.short_description

        version: None | str
        version = self.version

        last_run: dict[str, Any] | Unset = UNSET
        if not isinstance(self.last_run, Unset):
            last_run = self.last_run.to_dict()

        run_results: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run_results, Unset):
            run_results = self.run_results.to_dict()

        slug = self.slug

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        subdomain = self.subdomain

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "health_status": health_status,
                "is_externally_accessible": is_externally_accessible,
                "name": name,
                "next_run_at": next_run_at,
                "owner": owner,
                "pending_timeout": pending_timeout,
                "running_timeout": running_timeout,
                "schedule": schedule,
                "short_description": short_description,
                "version": version,
            }
        )
        if last_run is not UNSET:
            field_dict["last_run"] = last_run
        if run_results is not UNSET:
            field_dict["run_results"] = run_results
        if slug is not UNSET:
            field_dict["slug"] = slug
        if status is not UNSET:
            field_dict["status"] = status
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run
        from ..models.run_results import RunResults

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        health_status = AppHealthStatus(d.pop("health_status"))

        is_externally_accessible = d.pop("is_externally_accessible")

        name = d.pop("name")

        def _parse_next_run_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_run_at_type_0 = isoparse(data)

                return next_run_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        next_run_at = _parse_next_run_at(d.pop("next_run_at"))

        owner = d.pop("owner")

        pending_timeout = d.pop("pending_timeout")

        running_timeout = d.pop("running_timeout")

        def _parse_schedule(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        schedule = _parse_schedule(d.pop("schedule"))

        short_description = d.pop("short_description")

        def _parse_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        version = _parse_version(d.pop("version"))

        _last_run = d.pop("last_run", UNSET)
        last_run: Run | Unset
        if isinstance(_last_run, Unset):
            last_run = UNSET
        else:
            last_run = Run.from_dict(_last_run)

        _run_results = d.pop("run_results", UNSET)
        run_results: RunResults | Unset
        if isinstance(_run_results, Unset):
            run_results = UNSET
        else:
            run_results = RunResults.from_dict(_run_results)

        slug = d.pop("slug", UNSET)

        _status = d.pop("status", UNSET)
        status: AppStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = AppStatus(_status)

        subdomain = d.pop("subdomain", UNSET)

        app = cls(
            created_at=created_at,
            health_status=health_status,
            is_externally_accessible=is_externally_accessible,
            name=name,
            next_run_at=next_run_at,
            owner=owner,
            pending_timeout=pending_timeout,
            running_timeout=running_timeout,
            schedule=schedule,
            short_description=short_description,
            version=version,
            last_run=last_run,
            run_results=run_results,
            slug=slug,
            status=status,
            subdomain=subdomain,
        )

        return app
