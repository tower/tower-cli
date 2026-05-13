from enum import Enum


class UsageMetricTimeSeriesPointName(str, Enum):
    RUN_SECONDS = "run_seconds"

    def __str__(self) -> str:
        return str(self.value)
