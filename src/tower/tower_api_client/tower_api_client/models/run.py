import datetime
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="Run")


@_attrs_define
class Run:
    """
    Attributes:
        app_name (str):
        cancelled_at (Union[None, datetime.datetime]):
        created_at (datetime.datetime):
        ended_at (Union[None, datetime.datetime]):
        number (int):
        scheduled_at (datetime.datetime):
        started_at (Union[None, datetime.datetime]):
        status (str):
    """

    app_name: str
    cancelled_at: Union[None, datetime.datetime]
    created_at: datetime.datetime
    ended_at: Union[None, datetime.datetime]
    number: int
    scheduled_at: datetime.datetime
    started_at: Union[None, datetime.datetime]
    status: str

    def to_dict(self) -> dict[str, Any]:
        app_name = self.app_name

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

        number = self.number

        scheduled_at = self.scheduled_at.isoformat()

        started_at: Union[None, str]
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app_name": app_name,
                "cancelled_at": cancelled_at,
                "created_at": created_at,
                "ended_at": ended_at,
                "number": number,
                "scheduled_at": scheduled_at,
                "started_at": started_at,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        app_name = d.pop("app_name")

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

        number = d.pop("number")

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

        status = d.pop("status")

        run = cls(
            app_name=app_name,
            cancelled_at=cancelled_at,
            created_at=created_at,
            ended_at=ended_at,
            number=number,
            scheduled_at=scheduled_at,
            started_at=started_at,
            status=status,
        )

        return run
