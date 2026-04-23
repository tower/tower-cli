from enum import Enum


class InviteTeamMemberParamsRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"

    def __str__(self) -> str:
        return str(self.value)
