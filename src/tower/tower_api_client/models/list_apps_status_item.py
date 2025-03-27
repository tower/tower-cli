from enum import Enum


class ListAppsStatusItem(str, Enum):
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
