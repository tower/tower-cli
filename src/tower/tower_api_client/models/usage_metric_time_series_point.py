from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.usage_metric_time_series_point_name import UsageMetricTimeSeriesPointName

T = TypeVar("T", bound="UsageMetricTimeSeriesPoint")


@_attrs_define
class UsageMetricTimeSeriesPoint:
    """
    Attributes:
        date (datetime.datetime):
        name (UsageMetricTimeSeriesPointName):
        value (int):
    """

    date: datetime.datetime
    name: UsageMetricTimeSeriesPointName
    value: int

    def to_dict(self) -> dict[str, Any]:
        date = self.date.isoformat()

        name = self.name.value

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "date": date,
                "name": name,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        date = isoparse(d.pop("date"))

        name = UsageMetricTimeSeriesPointName(d.pop("name"))

        value = d.pop("value")

        usage_metric_time_series_point = cls(
            date=date,
            name=name,
            value=value,
        )

        return usage_metric_time_series_point
