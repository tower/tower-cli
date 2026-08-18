from enum import Enum


class CatalogFactConfidence(str, Enum):
    CONFIRMED = "confirmed"
    HEURISTIC = "heuristic"
    INFERRED = "inferred"

    def __str__(self) -> str:
        return str(self.value)
