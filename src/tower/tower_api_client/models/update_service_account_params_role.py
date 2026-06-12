from enum import Enum


class UpdateServiceAccountParamsRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"

    def __str__(self) -> str:
        return str(self.value)
