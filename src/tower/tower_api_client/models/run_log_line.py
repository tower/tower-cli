import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="RunLogLine")


@_attrs_define
class RunLogLine:
    """
    Attributes:
        channel (str):
        message (str):
        timestamp (datetime.datetime):
    """

    channel: str
    message: str
    timestamp: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        channel = self.channel

        message = self.message

        timestamp = self.timestamp.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "channel": channel,
                "message": message,
                "timestamp": timestamp,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        channel = d.pop("channel")

        message = d.pop("message")

        timestamp = isoparse(d.pop("timestamp"))

        run_log_line = cls(
            channel=channel,
            message=message,
            timestamp=timestamp,
        )

        return run_log_line
