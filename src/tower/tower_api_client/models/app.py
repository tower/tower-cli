import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.app_status import AppStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="App")


@_attrs_define
class App:
    """
    Attributes:
        created_at (datetime.datetime): The date and time this app was created.
        name (str): The name of the app.
        next_run_at (Union[None, datetime.datetime]): The next time this app will run as part of it's schedule, null if
            none.
        owner (str): The account slug that owns this app
        schedule (Union[None, str]): The schedule associated with this app, null if none.
        short_description (str): A short description of the app. Can be empty.
        slug (str): The unique slug of the app.
        version (Union[None, str]): The current version of this app, null if none.
        last_run (Union[Unset, Run]):
        status (Union[Unset, AppStatus]): The status of the app
    """

    created_at: datetime.datetime
    name: str
    next_run_at: Union[None, datetime.datetime]
    owner: str
    schedule: Union[None, str]
    short_description: str
    slug: str
    version: Union[None, str]
    last_run: Union[Unset, "Run"] = UNSET
    status: Union[Unset, AppStatus] = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        name = self.name

        next_run_at: Union[None, str]
        if isinstance(self.next_run_at, datetime.datetime):
            next_run_at = self.next_run_at.isoformat()
        else:
            next_run_at = self.next_run_at

        owner = self.owner

        schedule: Union[None, str]
        schedule = self.schedule

        short_description = self.short_description

        slug = self.slug

        version: Union[None, str]
        version = self.version

        last_run: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.last_run, Unset):
            last_run = self.last_run.to_dict()

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "name": name,
                "next_run_at": next_run_at,
                "owner": owner,
                "schedule": schedule,
                "short_description": short_description,
                "slug": slug,
                "version": version,
            }
        )
        if last_run is not UNSET:
            field_dict["last_run"] = last_run
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        name = d.pop("name")

        def _parse_next_run_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_run_at_type_0 = isoparse(data)

                return next_run_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        next_run_at = _parse_next_run_at(d.pop("next_run_at"))

        owner = d.pop("owner")

        def _parse_schedule(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        schedule = _parse_schedule(d.pop("schedule"))

        short_description = d.pop("short_description")

        slug = d.pop("slug")

        def _parse_version(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        version = _parse_version(d.pop("version"))

        _last_run = d.pop("last_run", UNSET)
        last_run: Union[Unset, Run]
        if isinstance(_last_run, Unset):
            last_run = UNSET
        else:
            last_run = Run.from_dict(_last_run)

        _status = d.pop("status", UNSET)
        status: Union[Unset, AppStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = AppStatus(_status)

        app = cls(
            created_at=created_at,
            name=name,
            next_run_at=next_run_at,
            owner=owner,
            schedule=schedule,
            short_description=short_description,
            slug=slug,
            version=version,
            last_run=last_run,
            status=status,
        )

        return app
