from enum import Enum


class ListAppsSort(str, Enum):
    A_TO_Z = "a_to_z"
    CREATED_AT = "created_at"
    MOST_RECENT_RUN = "most_recent_run"
    UPDATED_AT = "updated_at"

    def __str__(self) -> str:
        return str(self.value)
