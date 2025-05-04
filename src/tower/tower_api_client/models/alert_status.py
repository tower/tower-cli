from enum import Enum


class AlertStatus(str, Enum):
    ERRORED = "errored"
    PENDING = "pending"
    SENT = "sent"

    def __str__(self) -> str:
        return str(self.value)
