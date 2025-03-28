from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="StatisticsSettings")


@attr.s(auto_attribs=True)
class StatisticsSettings:
    """
    Attributes:
        period (str):
    """

    period: str

    def to_dict(self) -> Dict[str, Any]:
        period = self.period

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "period": period,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        period = d.pop("period")

        statistics_settings = cls(
            period=period,
        )

        return statistics_settings
