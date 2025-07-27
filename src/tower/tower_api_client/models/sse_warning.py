import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="SSEWarning")


@_attrs_define
class SSEWarning:
    """
    Attributes:
        content (str): Contents of the warning.
        reported_at (datetime.datetime): Timestamp of the event.
    """

    content: str
    reported_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        reported_at = self.reported_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "content": content,
                "reported_at": reported_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content = d.pop("content")

        reported_at = isoparse(d.pop("reported_at"))

        sse_warning = cls(
            content=content,
            reported_at=reported_at,
        )

        return sse_warning
