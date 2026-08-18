from enum import Enum


class CatalogFactScope(str, Enum):
    CATALOG = "catalog"
    COLUMN = "column"
    METRIC = "metric"
    NAMESPACE = "namespace"
    TABLE = "table"

    def __str__(self) -> str:
        return str(self.value)
