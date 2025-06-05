from enum import Enum


class SearchRunsStatusItem(str, Enum):
    CANCELLED = "cancelled"
    CRASHED = "crashed"
    ERRORED = "errored"
    EXITED = "exited"
    PENDING = "pending"
    RUNNING = "running"
    SCHEDULED = "scheduled"
    VALUE_7 = ""

    def __str__(self) -> str:
        return str(self.value)
