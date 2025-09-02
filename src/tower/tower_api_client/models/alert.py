import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.run_failure_alert import RunFailureAlert


T = TypeVar("T", bound="Alert")


@_attrs_define
class Alert:
    """
    Attributes:
        acked (bool):
        alert_type (str):
        created_at (datetime.datetime):
        detail (RunFailureAlert):
        environment (str):
        seq (int):
        status (str):
    """

    acked: bool
    alert_type: str
    created_at: datetime.datetime
    detail: "RunFailureAlert"
    environment: str
    seq: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        acked = self.acked

        alert_type = self.alert_type

        created_at = self.created_at.isoformat()

        detail = self.detail.to_dict()

        environment = self.environment

        seq = self.seq

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "acked": acked,
                "alert_type": alert_type,
                "created_at": created_at,
                "detail": detail,
                "environment": environment,
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

        environment = d.pop("environment")

        seq = d.pop("seq")

        status = d.pop("status")

        alert = cls(
            acked=acked,
            alert_type=alert_type,
            created_at=created_at,
            detail=detail,
            environment=environment,
            seq=seq,
            status=status,
        )

        return alert
