import datetime
from typing import Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="LogLineError")


@attr.s(auto_attribs=True)
class LogLineError:
    """
    Attributes:
        content (str): Contents of the error.
        reported_at (datetime.datetime): Timestamp of the event.
    """

    content: str
    reported_at: datetime.datetime

    def to_dict(self) -> Dict[str, Any]:
        content = self.content
        reported_at = self.reported_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "content": content,
                "reported_at": reported_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        content = d.pop("content")

        reported_at = isoparse(d.pop("reported_at"))

        log_line_error = cls(
            content=content,
            reported_at=reported_at,
        )

        return log_line_error
