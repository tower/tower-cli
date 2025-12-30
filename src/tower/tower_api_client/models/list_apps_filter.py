from enum import Enum


class ListAppsFilter(str, Enum):
    DISABLED = "disabled"
    HEALTHY = "healthy"
    RUNNING = "running"
    WITHWARNING = "withWarning"

    def __str__(self) -> str:
        return str(self.value)
