from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="ListTeamMembersResponse")


@_attrs_define
class ListTeamMembersResponse:
    """
    Attributes:
        team_members (list['User']): All of the members of a team
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListTeamMembersResponse.json.
    """

    team_members: list["User"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        team_members = []
        for team_members_item_data in self.team_members:
            team_members_item = team_members_item_data.to_dict()
            team_members.append(team_members_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "team_members": team_members,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User

        d = dict(src_dict)
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
