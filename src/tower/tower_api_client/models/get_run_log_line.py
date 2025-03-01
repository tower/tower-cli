import datetime
from typing import Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="GetRunLogLine")


@attr.s(auto_attribs=True)
class GetRunLogLine:
    """
    Attributes:
        message (str):
        timestamp (datetime.datetime):
    """

    message: str
    timestamp: datetime.datetime

    def to_dict(self) -> Dict[str, Any]:
        message = self.message
        timestamp = self.timestamp.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "message": message,
                "timestamp": timestamp,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        message = d.pop("message")

        timestamp = isoparse(d.pop("timestamp"))

        get_run_log_line = cls(
            message=message,
            timestamp=timestamp,
        )

        return get_run_log_line
