from enum import Enum


class GenerateRunStatisticsStatusItem(str, Enum):
    CANCELLED = "cancelled"
    CRASHED = "crashed"
    ERRORED = "errored"
    EXITED = "exited"
    PENDING = "pending"
    RUNNING = "running"
    SCHEDULED = "scheduled"

    def __str__(self) -> str:
        return str(self.value)
