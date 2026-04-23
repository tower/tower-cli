from enum import Enum


class StatisticsSettingsInterval(str, Enum):
    DAILY = "daily"
    HOURLY = "hourly"

    def __str__(self) -> str:
        return str(self.value)
