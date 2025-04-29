from enum import Enum


class AppStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
