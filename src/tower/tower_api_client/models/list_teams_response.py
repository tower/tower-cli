from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team import Team


T = TypeVar("T", bound="ListTeamsResponse")


@_attrs_define
class ListTeamsResponse:
    """
    Attributes:
        teams (list['Team']): List of teams
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListTeamsResponse.json.
    """

    teams: list["Team"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        teams = []
        for teams_item_data in self.teams:
            teams_item = teams_item_data.to_dict()
            teams.append(teams_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "teams": teams,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team import Team

        d = dict(src_dict)
        teams = []
        _teams = d.pop("teams")
        for teams_item_data in _teams:
            teams_item = Team.from_dict(teams_item_data)

            teams.append(teams_item)

        schema = d.pop("$schema", UNSET)

        list_teams_response = cls(
            teams=teams,
            schema=schema,
        )

        return list_teams_response
