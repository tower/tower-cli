import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="App")


@attr.s(auto_attribs=True)
class App:
    """
    Attributes:
        created_at (datetime.datetime): The date and time this app was created.
        name (str): The name of the app.
        owner (str): The account slug that owns this app
        short_description (str): A short description of the app. Can be empty.
        last_run (Union[Unset, Run]):
        next_run_at (Optional[datetime.datetime]): The next time this app will run as part of it's schedule, null if
            none.
        schedule (Optional[str]): The schedule associated with this app, null if none.
        status (Union[Unset, str]): The status of the app
        version (Optional[str]): The current version of this app, null if none.
    """

    created_at: datetime.datetime
    name: str
    owner: str
    short_description: str
    next_run_at: Optional[datetime.datetime]
    schedule: Optional[str]
    version: Optional[str]
    last_run: Union[Unset, "Run"] = UNSET
    status: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        created_at = self.created_at.isoformat()

        name = self.name
        owner = self.owner
        short_description = self.short_description
        last_run: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.last_run, Unset):
            last_run = self.last_run.to_dict()

        next_run_at = self.next_run_at.isoformat() if self.next_run_at else None

        schedule = self.schedule
        status = self.status
        version = self.version

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "name": name,
                "owner": owner,
                "short_description": short_description,
                "next_run_at": next_run_at,
                "schedule": schedule,
                "version": version,
            }
        )
        if last_run is not UNSET:
            field_dict["last_run"] = last_run
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.run import Run

        d = src_dict.copy()
        created_at = isoparse(d.pop("created_at"))

        name = d.pop("name")

        owner = d.pop("owner")

        short_description = d.pop("short_description")

        _last_run = d.pop("last_run", UNSET)
        last_run: Union[Unset, Run]
        if isinstance(_last_run, Unset):
            last_run = UNSET
        else:
            last_run = Run.from_dict(_last_run)

        _next_run_at = d.pop("next_run_at")
        next_run_at: Optional[datetime.datetime]
        if _next_run_at is None:
            next_run_at = None
        else:
            next_run_at = isoparse(_next_run_at)

        schedule = d.pop("schedule")

        status = d.pop("status", UNSET)

        version = d.pop("version")

        app = cls(
            created_at=created_at,
            name=name,
            owner=owner,
            short_description=short_description,
            last_run=last_run,
            next_run_at=next_run_at,
            schedule=schedule,
            status=status,
            version=version,
        )

        return app
