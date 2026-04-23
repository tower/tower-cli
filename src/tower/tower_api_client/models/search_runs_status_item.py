from enum import Enum


class SearchRunsStatusItem(str, Enum):
    CANCELLED = "cancelled"
    CRASHED = "crashed"
    ERRORED = "errored"
    EXITED = "exited"
    PENDING = "pending"
    RETRYING = "retrying"
    RUNNING = "running"
    STARTING = "starting"

    def __str__(self) -> str:
        return str(self.value)
