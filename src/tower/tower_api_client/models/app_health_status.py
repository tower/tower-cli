from enum import Enum


class AppHealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
