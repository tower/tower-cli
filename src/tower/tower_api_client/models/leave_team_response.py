from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="LeaveTeamResponse")


@_attrs_define
class LeaveTeamResponse:
    """
    Attributes:
        team (Team):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/LeaveTeamResponse.json.
    """

    team: "Team"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        team = self.team.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "team": team,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team

        d = dict(src_dict)
        team = Team.from_dict(d.pop("team"))

        schema = d.pop("$schema", UNSET)

        leave_team_response = cls(
            team=team,
            schema=schema,
        )

        return leave_team_response
