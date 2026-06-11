from enum import Enum


class VendCatalogCredentialsBodyMode(str, Enum):
    READ = "read"
    READ_WRITE = "read-write"

    def __str__(self) -> str:
        return str(self.value)
