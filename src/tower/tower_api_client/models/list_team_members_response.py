from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="ListTeamMembersResponse")


@attr.s(auto_attribs=True)
class ListTeamMembersResponse:
    """
    Attributes:
        team_members (List['User']): All of the members of a team
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListTeamMembersResponse.json.
    """

    team_members: List["User"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        team_members = []
        for team_members_item_data in self.team_members:
            team_members_item = team_members_item_data.to_dict()

            team_members.append(team_members_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "team_members": team_members,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user import User

        d = src_dict.copy()
        team_members = []
        _team_members = d.pop("team_members")
        for team_members_item_data in _team_members:
            team_members_item = User.from_dict(team_members_item_data)

            team_members.append(team_members_item)

        schema = d.pop("$schema", UNSET)

        list_team_members_response = cls(
            team_members=team_members,
            schema=schema,
        )

        return list_team_members_response
