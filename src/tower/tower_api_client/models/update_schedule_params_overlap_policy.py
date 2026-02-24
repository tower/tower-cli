from enum import Enum


class UpdateScheduleParamsOverlapPolicy(str, Enum):
    ALLOW = "allow"
    SKIP = "skip"

    def __str__(self) -> str:
        return str(self.value)
