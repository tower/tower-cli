from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.shoulder_tap import ShoulderTap


T = TypeVar("T", bound="StreamShouldertapsEventShouldertap")


@_attrs_define
class StreamShouldertapsEventShouldertap:
    """
    Attributes:
        data (ShoulderTap):
        event (Literal['shouldertap']): The event name.
        id (int | Unset): The event ID.
        retry (int | Unset): The retry time in milliseconds.
    """

    data: ShoulderTap
    event: Literal["shouldertap"]
    id: int | Unset = UNSET
    retry: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        event = self.event

        id = self.id

        retry = self.retry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "event": event,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.shoulder_tap import ShoulderTap

        d = dict(src_dict)
        data = ShoulderTap.from_dict(d.pop("data"))

        event = cast(Literal["shouldertap"], d.pop("event"))
        if event != "shouldertap":
            raise ValueError(f"event must match const 'shouldertap', got '{event}'")

        id = d.pop("id", UNSET)

        retry = d.pop("retry", UNSET)

        stream_shouldertaps_event_shouldertap = cls(
            data=data,
            event=event,
            id=id,
            retry=retry,
        )

        stream_shouldertaps_event_shouldertap.additional_properties = d
        return stream_shouldertaps_event_shouldertap

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
