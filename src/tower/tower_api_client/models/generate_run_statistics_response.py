from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_statistics import RunStatistics
    from ..models.series_point import SeriesPoint
    from ..models.statistics_settings import StatisticsSettings


T = TypeVar("T", bound="GenerateRunStatisticsResponse")


@attr.s(auto_attribs=True)
class GenerateRunStatisticsResponse:
    """
    Attributes:
        series (List['SeriesPoint']):
        settings (StatisticsSettings):
        stats (RunStatistics):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/GenerateRunStatisticsResponse.json.
    """

    series: List["SeriesPoint"]
    settings: "StatisticsSettings"
    stats: "RunStatistics"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        series = []
        for series_item_data in self.series:
            series_item = series_item_data.to_dict()

            series.append(series_item)

        settings = self.settings.to_dict()

        stats = self.stats.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.run_statistics import RunStatistics
        from ..models.series_point import SeriesPoint
        from ..models.statistics_settings import StatisticsSettings

        d = src_dict.copy()
        series = []
        _series = d.pop("series")
        for series_item_data in _series:
            series_item = SeriesPoint.from_dict(series_item_data)

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
