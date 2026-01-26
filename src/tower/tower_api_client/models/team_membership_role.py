from enum import Enum


class TeamMembershipRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"

    def __str__(self) -> str:
        return str(self.value)
