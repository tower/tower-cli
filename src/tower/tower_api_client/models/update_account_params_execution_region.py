from enum import Enum


class UpdateAccountParamsExecutionRegion(str, Enum):
    AP_NORTHEAST_1 = "ap-northeast-1"
    AP_SOUTHEAST_2 = "ap-southeast-2"
    EU_CENTRAL_1 = "eu-central-1"
    EU_WEST_1 = "eu-west-1"
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"

    def __str__(self) -> str:
        return str(self.value)
