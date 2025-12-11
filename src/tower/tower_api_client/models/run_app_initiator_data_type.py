from enum import Enum


class RunAppInitiatorDataType(str, Enum):
    TOWER_CLI = "tower_cli"
    TOWER_RUN = "tower_run"
    TOWER_UI = "tower_ui"

    def __str__(self) -> str:
        return str(self.value)
