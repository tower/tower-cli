import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.alert_alert_type import AlertAlertType
from ..models.alert_status import AlertStatus

if TYPE_CHECKING:
    from ..models.alert_detail import AlertDetail


T = TypeVar("T", bound="Alert")


@_attrs_define
class Alert:
    """
    Attributes:
        alert_type (AlertAlertType): Type of the alert
        created_at (datetime.datetime): Time when the alert was created
        details (list['AlertDetail']): Detailed description of the alert
        id (str): Unique identifier for the alert
        status (AlertStatus): Status of the alert
    """

    alert_type: AlertAlertType
    created_at: datetime.datetime
    details: list["AlertDetail"]
    id: str
    status: AlertStatus

    def to_dict(self) -> dict[str, Any]:
        alert_type = self.alert_type.value

        created_at = self.created_at.isoformat()

        details = []
        for details_item_data in self.details:
            details_item = details_item_data.to_dict()
            details.append(details_item)

        id = self.id

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "alert_type": alert_type,
                "created_at": created_at,
                "details": details,
                "id": id,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_detail import AlertDetail

        d = dict(src_dict)
        alert_type = AlertAlertType(d.pop("alert_type"))

        created_at = isoparse(d.pop("created_at"))

        details = []
        _details = d.pop("details")
        for details_item_data in _details:
            details_item = AlertDetail.from_dict(details_item_data)

            details.append(details_item)

        id = d.pop("id")

        status = AlertStatus(d.pop("status"))

        alert = cls(
            alert_type=alert_type,
            created_at=created_at,
            details=details,
            id=id,
            status=status,
        )

        return alert
