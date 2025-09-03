from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
    Union,
    cast,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_failure_alert import RunFailureAlert


T = TypeVar("T", bound="StreamAlertsEventRunFailureAlert")


@_attrs_define
class StreamAlertsEventRunFailureAlert:
    """
    Attributes:
        data (RunFailureAlert):
        event (Literal['run_failure_alert']): The event name.
        id (Union[Unset, int]): The event ID.
        retry (Union[Unset, int]): The retry time in milliseconds.
    """

    data: "RunFailureAlert"
    event: Literal["run_failure_alert"]
    id: Union[Unset, int] = UNSET
    retry: Union[Unset, int] = UNSET
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
        from ..models.run_failure_alert import RunFailureAlert

        d = dict(src_dict)
        data = RunFailureAlert.from_dict(d.pop("data"))

        event = cast(Literal["run_failure_alert"], d.pop("event"))
        if event != "run_failure_alert":
            raise ValueError(
                f"event must match const 'run_failure_alert', got '{event}'"
            )

        id = d.pop("id", UNSET)

        retry = d.pop("retry", UNSET)

        stream_alerts_event_run_failure_alert = cls(
            data=data,
            event=event,
            id=id,
            retry=retry,
        )

        stream_alerts_event_run_failure_alert.additional_properties = d
        return stream_alerts_event_run_failure_alert

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
