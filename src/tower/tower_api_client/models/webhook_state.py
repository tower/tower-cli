from enum import Enum


class WebhookState(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
