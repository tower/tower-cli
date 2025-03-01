from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_statistics import AppStatistics


T = TypeVar("T", bound="GenerateAppStatisticsResponse")


@attr.s(auto_attribs=True)
class GenerateAppStatisticsResponse:
    """
    Attributes:
        statistics (AppStatistics):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/GenerateAppStatisticsResponse.json.
    """

    statistics: "AppStatistics"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        statistics = self.statistics.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "statistics": statistics,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app_statistics import AppStatistics

        d = src_dict.copy()
        statistics = AppStatistics.from_dict(d.pop("statistics"))

        schema = d.pop("$schema", UNSET)

        generate_app_statistics_response = cls(
            statistics=statistics,
            schema=schema,
        )

        return generate_app_statistics_response
