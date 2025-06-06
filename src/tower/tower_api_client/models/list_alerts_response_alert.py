import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.run_failure_alert import RunFailureAlert


T = TypeVar("T", bound="ListAlertsResponseAlert")


@_attrs_define
class ListAlertsResponseAlert:
    """
    Attributes:
        acked (bool): Whether the alert has been acknowledged
        alert_type (str): Type of the alert
        created_at (datetime.datetime): When the alert was created
        detail (RunFailureAlert):
        seq (int): Sequence number of the alert
        status (str): Current status of the alert
    """

    acked: bool
    alert_type: str
    created_at: datetime.datetime
    detail: "RunFailureAlert"
    seq: int
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        acked = self.acked

        alert_type = self.alert_type

        created_at = self.created_at.isoformat()

        detail = self.detail.to_dict()

        seq = self.seq

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "acked": acked,
                "alert_type": alert_type,
                "created_at": created_at,
                "detail": detail,
                "seq": seq,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_failure_alert import RunFailureAlert

        d = dict(src_dict)
        acked = d.pop("acked")

        alert_type = d.pop("alert_type")

        created_at = isoparse(d.pop("created_at"))

        detail = RunFailureAlert.from_dict(d.pop("detail"))

        seq = d.pop("seq")

        status = d.pop("status")

        list_alerts_response_alert = cls(
            acked=acked,
            alert_type=alert_type,
            created_at=created_at,
            detail=detail,
            seq=seq,
            status=status,
        )

        list_alerts_response_alert.additional_properties = d
        return list_alerts_response_alert

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
