from enum import Enum


class UpdateAccountParamsExecutionRegion(str, Enum):
    EU_CENTRAL_1 = "eu-central-1"
    US_EAST_1 = "us-east-1"

    def __str__(self) -> str:
        return str(self.value)
