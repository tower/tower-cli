from enum import Enum


class RunStatusGroup(str, Enum):
    FAILED = "failed"
    SUCCESSFUL = "successful"
    VALUE_2 = ""

    def __str__(self) -> str:
        return str(self.value)
