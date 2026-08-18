from enum import Enum


class TagFilterOp(str, Enum):
    EQ = "eq"
    IN = "in"
    NOTIN = "notIn"

    def __str__(self) -> str:
        return str(self.value)
