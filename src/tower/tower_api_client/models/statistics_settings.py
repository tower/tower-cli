import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.statistics_settings_interval import StatisticsSettingsInterval

T = TypeVar("T", bound="StatisticsSettings")


@_attrs_define
class StatisticsSettings:
    """
    Attributes:
        end_at (datetime.datetime): The end time for the statistics period.
        environment (str): The environment to get statistics for.
        interval (StatisticsSettingsInterval): The interval for the statistics period.
        start_at (datetime.datetime): The start time for the statistics period.
        timezone (str): The time zone for the statistics period.
    """

    end_at: datetime.datetime
    environment: str
    interval: StatisticsSettingsInterval
    start_at: datetime.datetime
    timezone: str

    def to_dict(self) -> dict[str, Any]:
        end_at = self.end_at.isoformat()

        environment = self.environment

        interval = self.interval.value

        start_at = self.start_at.isoformat()

        timezone = self.timezone

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "end_at": end_at,
                "environment": environment,
                "interval": interval,
                "start_at": start_at,
                "timezone": timezone,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        end_at = isoparse(d.pop("end_at"))

        environment = d.pop("environment")

        interval = StatisticsSettingsInterval(d.pop("interval"))

        start_at = isoparse(d.pop("start_at"))

        timezone = d.pop("timezone")

        statistics_settings = cls(
            end_at=end_at,
            environment=environment,
            interval=interval,
            start_at=start_at,
            timezone=timezone,
        )

        return statistics_settings
