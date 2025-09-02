from enum import Enum


class GetFeatureFlagResponseBodyValueType(str, Enum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    OBJECT = "object"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
