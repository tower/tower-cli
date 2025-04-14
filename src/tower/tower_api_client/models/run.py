import datetime
from typing import Any, Dict, Optional, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="Run")


@attr.s(auto_attribs=True)
class Run:
    """
    Attributes:
        app_name (str):
        created_at (datetime.datetime):
        environment (str):
        number (int):
        run_id (str):
        scheduled_at (datetime.datetime):
        status (str):
        status_group (str):
        cancelled_at (Optional[datetime.datetime]):
        ended_at (Optional[datetime.datetime]):
        started_at (Optional[datetime.datetime]):
    """

    app_name: str
    created_at: datetime.datetime
    environment: str
    number: int
    run_id: str
    scheduled_at: datetime.datetime
    status: str
    status_group: str
    cancelled_at: Optional[datetime.datetime]
    ended_at: Optional[datetime.datetime]
    started_at: Optional[datetime.datetime]

    def to_dict(self) -> Dict[str, Any]:
        app_name = self.app_name
        created_at = self.created_at.isoformat()

        environment = self.environment
        number = self.number
        run_id = self.run_id
        scheduled_at = self.scheduled_at.isoformat()

        status = self.status
        status_group = self.status_group
        cancelled_at = self.cancelled_at.isoformat() if self.cancelled_at else None

        ended_at = self.ended_at.isoformat() if self.ended_at else None

        started_at = self.started_at.isoformat() if self.started_at else None

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "app_name": app_name,
                "created_at": created_at,
                "environment": environment,
                "number": number,
                "run_id": run_id,
                "scheduled_at": scheduled_at,
                "status": status,
                "status_group": status_group,
                "cancelled_at": cancelled_at,
                "ended_at": ended_at,
                "started_at": started_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        app_name = d.pop("app_name")

        created_at = isoparse(d.pop("created_at"))

        environment = d.pop("environment")

        number = d.pop("number")

        run_id = d.pop("run_id")

        scheduled_at = isoparse(d.pop("scheduled_at"))

        status = d.pop("status")

        status_group = d.pop("status_group")

        _cancelled_at = d.pop("cancelled_at")
        cancelled_at: Optional[datetime.datetime]
        if _cancelled_at is None:
            cancelled_at = None
        else:
            cancelled_at = isoparse(_cancelled_at)

        _ended_at = d.pop("ended_at")
        ended_at: Optional[datetime.datetime]
        if _ended_at is None:
            ended_at = None
        else:
            ended_at = isoparse(_ended_at)

        _started_at = d.pop("started_at")
        started_at: Optional[datetime.datetime]
        if _started_at is None:
            started_at = None
        else:
            started_at = isoparse(_started_at)

        run = cls(
            app_name=app_name,
            created_at=created_at,
            environment=environment,
            number=number,
            run_id=run_id,
            scheduled_at=scheduled_at,
            status=status,
            status_group=status_group,
            cancelled_at=cancelled_at,
            ended_at=ended_at,
            started_at=started_at,
        )

        return run
