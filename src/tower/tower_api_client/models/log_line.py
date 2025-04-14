import datetime
from typing import Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="LogLine")


@attr.s(auto_attribs=True)
class LogLine:
    """
    Attributes:
        content (str): Contents of the log message.
        line_num (int): Line number.
        reported_at (datetime.datetime): Timestamp of the log line.
        run_id (str): The uuid of the Run.
    """

    content: str
    line_num: int
    reported_at: datetime.datetime
    run_id: str

    def to_dict(self) -> Dict[str, Any]:
        content = self.content
        line_num = self.line_num
        reported_at = self.reported_at.isoformat()

        run_id = self.run_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "content": content,
                "line_num": line_num,
                "reported_at": reported_at,
                "run_id": run_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        content = d.pop("content")

        line_num = d.pop("line_num")

        reported_at = isoparse(d.pop("reported_at"))

        run_id = d.pop("run_id")

        log_line = cls(
            content=content,
            line_num=line_num,
            reported_at=reported_at,
            run_id=run_id,
        )

        return log_line
