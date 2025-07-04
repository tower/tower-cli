from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_statistics import RunStatistics
    from ..models.run_timeseries_point import RunTimeseriesPoint
    from ..models.statistics_settings import StatisticsSettings


T = TypeVar("T", bound="GenerateRunStatisticsResponse")


@_attrs_define
class GenerateRunStatisticsResponse:
    """
    Attributes:
        series (list['RunTimeseriesPoint']):
        settings (StatisticsSettings):
        stats (RunStatistics):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/GenerateRunStatisticsResponse.json.
    """

    series: list["RunTimeseriesPoint"]
    settings: "StatisticsSettings"
    stats: "RunStatistics"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        series = []
        for series_item_data in self.series:
            series_item = series_item_data.to_dict()
            series.append(series_item)

        settings = self.settings.to_dict()

        stats = self.stats.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "series": series,
                "settings": settings,
                "stats": stats,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_statistics import RunStatistics
        from ..models.run_timeseries_point import RunTimeseriesPoint
        from ..models.statistics_settings import StatisticsSettings

        d = dict(src_dict)
        series = []
        _series = d.pop("series")
        for series_item_data in _series:
            series_item = RunTimeseriesPoint.from_dict(series_item_data)

            series.append(series_item)

        settings = StatisticsSettings.from_dict(d.pop("settings"))

        stats = RunStatistics.from_dict(d.pop("stats"))

        schema = d.pop("$schema", UNSET)

        generate_run_statistics_response = cls(
            series=series,
            settings=settings,
            stats=stats,
            schema=schema,
        )

        return generate_run_statistics_response
