from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_statistics import AppStatistics


T = TypeVar("T", bound="GenerateAppStatisticsResponse")


@_attrs_define
class GenerateAppStatisticsResponse:
    """
    Attributes:
        statistics (AppStatistics):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/GenerateAppStatisticsResponse.json.
    """

    statistics: "AppStatistics"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        statistics = self.statistics.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "statistics": statistics,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_statistics import AppStatistics

        d = dict(src_dict)
        statistics = AppStatistics.from_dict(d.pop("statistics"))

        schema = d.pop("$schema", UNSET)

        generate_app_statistics_response = cls(
            statistics=statistics,
            schema=schema,
        )

        return generate_app_statistics_response
