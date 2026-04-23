from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.usage_metric_time_series_point import UsageMetricTimeSeriesPoint


T = TypeVar("T", bound="GenerateOrganizationUsageTimeSeriesResponse")


@_attrs_define
class GenerateOrganizationUsageTimeSeriesResponse:
    """
    Attributes:
        series (list[UsageMetricTimeSeriesPoint]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/GenerateOrganizationUsageTimeSeriesResponse.json.
    """

    series: list[UsageMetricTimeSeriesPoint]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        series = []
        for series_item_data in self.series:
            series_item = series_item_data.to_dict()
            series.append(series_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "series": series,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_metric_time_series_point import UsageMetricTimeSeriesPoint

        d = dict(src_dict)
        series = []
        _series = d.pop("series")
        for series_item_data in _series:
            series_item = UsageMetricTimeSeriesPoint.from_dict(series_item_data)

            series.append(series_item)

        schema = d.pop("$schema", UNSET)

        generate_organization_usage_time_series_response = cls(
            series=series,
            schema=schema,
        )

        return generate_organization_usage_time_series_response
