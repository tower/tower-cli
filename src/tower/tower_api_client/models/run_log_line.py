import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.run_log_line_channel import RunLogLineChannel
from ..types import UNSET, Unset

T = TypeVar("T", bound="RunLogLine")


@_attrs_define
class RunLogLine:
    """
    Attributes:
        channel (RunLogLineChannel): The channel this log line belongs to.
        content (str): Contents of the log message.
        line_num (int): Line number.
        reported_at (datetime.datetime): Timestamp of the log line.
        run_id (str): The uuid of the Run.
        message (Union[Unset, str]): This property is deprecated. Please use content instead.
        timestamp (Union[Unset, datetime.datetime]): This property is deprecated. Please use reported_at instead.
    """

    channel: RunLogLineChannel
    content: str
    line_num: int
    reported_at: datetime.datetime
    run_id: str
    message: Union[Unset, str] = UNSET
    timestamp: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        channel = self.channel.value

        content = self.content

        line_num = self.line_num

        reported_at = self.reported_at.isoformat()

        run_id = self.run_id

        message = self.message

        timestamp: Union[Unset, str] = UNSET
        if not isinstance(self.timestamp, Unset):
            timestamp = self.timestamp.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "channel": channel,
                "content": content,
                "line_num": line_num,
                "reported_at": reported_at,
                "run_id": run_id,
            }
        )
        if message is not UNSET:
            field_dict["message"] = message
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        channel = RunLogLineChannel(d.pop("channel"))

        content = d.pop("content")

        line_num = d.pop("line_num")

        reported_at = isoparse(d.pop("reported_at"))

        run_id = d.pop("run_id")

        message = d.pop("message", UNSET)

        _timestamp = d.pop("timestamp", UNSET)
        timestamp: Union[Unset, datetime.datetime]
        if isinstance(_timestamp, Unset):
            timestamp = UNSET
        else:
            timestamp = isoparse(_timestamp)

        run_log_line = cls(
            channel=channel,
            content=content,
            line_num=line_num,
            reported_at=reported_at,
            run_id=run_id,
            message=message,
            timestamp=timestamp,
        )

        return run_log_line
