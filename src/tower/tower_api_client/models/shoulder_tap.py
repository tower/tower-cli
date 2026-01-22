from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="ShoulderTap")


@_attrs_define
class ShoulderTap:
    """
    Attributes:
        account_id (str): Account ID that owns the resource.
        event_type (str): Event type in format resource.changed (e.g., apps.changed, runs.changed).
        resource_id (str): Unique identifier of the resource.
        resource_type (str): Type of resource (apps, runs, schedules, secrets, environments, catalogs).
        timestamp (datetime.datetime): Timestamp when the event occurred.
    """

    account_id: str
    event_type: str
    resource_id: str
    resource_type: str
    timestamp: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        account_id = self.account_id

        event_type = self.event_type

        resource_id = self.resource_id

        resource_type = self.resource_type

        timestamp = self.timestamp.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "account_id": account_id,
                "event_type": event_type,
                "resource_id": resource_id,
                "resource_type": resource_type,
                "timestamp": timestamp,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_id = d.pop("account_id")

        event_type = d.pop("event_type")

        resource_id = d.pop("resource_id")

        resource_type = d.pop("resource_type")

        timestamp = isoparse(d.pop("timestamp"))

        shoulder_tap = cls(
            account_id=account_id,
            event_type=event_type,
            resource_id=resource_id,
            resource_type=resource_type,
            timestamp=timestamp,
        )

        return shoulder_tap
