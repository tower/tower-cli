from enum import Enum


class RunCreatorType(str, Enum):
    SERVICE_ACCOUNT = "service_account"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
