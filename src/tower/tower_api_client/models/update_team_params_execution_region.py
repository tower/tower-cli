from enum import Enum


class UpdateTeamParamsExecutionRegion(str, Enum):
    EU_CENTRAL_1 = "eu-central-1"
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"

    def __str__(self) -> str:
        return str(self.value)
