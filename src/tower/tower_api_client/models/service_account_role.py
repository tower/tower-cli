from enum import Enum


class ServiceAccountRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"

    def __str__(self) -> str:
        return str(self.value)
