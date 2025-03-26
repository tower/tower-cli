from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="RemoveTeamMemberResponse")


@attr.s(auto_attribs=True)
class RemoveTeamMemberResponse:
    """
    Attributes:
        team_member (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/RemoveTeamMemberResponse.json.
    """

    team_member: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        team_member = self.team_member.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "team_member": team_member,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user import User

        d = src_dict.copy()
        team_member = User.from_dict(d.pop("team_member"))

        schema = d.pop("$schema", UNSET)

        remove_team_member_response = cls(
            team_member=team_member,
            schema=schema,
        )

        return remove_team_member_response
