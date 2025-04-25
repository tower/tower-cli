import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.log_line_channel import LogLineChannel

T = TypeVar("T", bound="LogLine")


@_attrs_define
class LogLine:
    """
    Attributes:
        channel (LogLineChannel): The channel (either Program or Setup) this log line belongs to.
        content (str): Contents of the log message.
        line_num (int): Line number.
        reported_at (datetime.datetime): Timestamp of the log line.
        run_id (str): The uuid of the Run.
    """

    channel: LogLineChannel
    content: str
    line_num: int
    reported_at: datetime.datetime
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        channel = self.channel.value

        content = self.content

        line_num = self.line_num

        reported_at = self.reported_at.isoformat()

        run_id = self.run_id

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        channel = LogLineChannel(d.pop("channel"))

        content = d.pop("content")

        line_num = d.pop("line_num")

        reported_at = isoparse(d.pop("reported_at"))

        run_id = d.pop("run_id")

        log_line = cls(
            channel=channel,
            content=content,
            line_num=line_num,
            reported_at=reported_at,
            run_id=run_id,
        )

        return log_line
