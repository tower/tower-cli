from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="CreateTeamResponse")


@attr.s(auto_attribs=True)
class CreateTeamResponse:
    """
    Attributes:
        team (Team):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateTeamResponse.json.
    """

    team: "Team"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        team = self.team.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "team": team,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.team import Team

        d = src_dict.copy()
        team = Team.from_dict(d.pop("team"))

        schema = d.pop("$schema", UNSET)

        create_team_response = cls(
            team=team,
            schema=schema,
        )

        return create_team_response
