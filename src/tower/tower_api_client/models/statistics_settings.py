from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="StatisticsSettings")


@_attrs_define
class StatisticsSettings:
    """
    Attributes:
        period (str):
    """

    period: str

    def to_dict(self) -> dict[str, Any]:
        period = self.period

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "period": period,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        period = d.pop("period")

        statistics_settings = cls(
            period=period,
        )

        return statistics_settings
