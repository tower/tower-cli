from enum import Enum


class UpdateCatalogFactBodyConfidence(str, Enum):
    CONFIRMED = "confirmed"
    HEURISTIC = "heuristic"
    INFERRED = "inferred"

    def __str__(self) -> str:
        return str(self.value)
