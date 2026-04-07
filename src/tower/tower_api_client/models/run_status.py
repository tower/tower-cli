from enum import Enum


class RunStatus(str, Enum):
    CANCELLED = "cancelled"
    CRASHED = "crashed"
    ERRORED = "errored"
    EXITED = "exited"
    PENDING = "pending"
    RETRYING = "retrying"
    RUNNING = "running"
    SCHEDULED = "scheduled"

    def __str__(self) -> str:
        return str(self.value)
