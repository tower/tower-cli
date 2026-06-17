from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SSEWarning")


@_attrs_define
class SSEWarning:
    """
    Attributes:
        content (str): Contents of the warning.
        reported_at (datetime.datetime): Timestamp of the event.
        end_of_stream (bool | Unset): When true, the server has delivered every log line and is closing the stream;
            clients should stop and not reconnect.
    """

    content: str
    reported_at: datetime.datetime
    end_of_stream: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        reported_at = self.reported_at.isoformat()

        end_of_stream = self.end_of_stream

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "content": content,
                "reported_at": reported_at,
            }
        )
        if end_of_stream is not UNSET:
            field_dict["end_of_stream"] = end_of_stream

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content = d.pop("content")

        reported_at = isoparse(d.pop("reported_at"))

        end_of_stream = d.pop("end_of_stream", UNSET)

        sse_warning = cls(
            content=content,
            reported_at=reported_at,
            end_of_stream=end_of_stream,
        )

        return sse_warning
