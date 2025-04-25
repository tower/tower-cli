from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="RemoveTeamMemberResponse")


@_attrs_define
class RemoveTeamMemberResponse:
    """
    Attributes:
        team_member (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RemoveTeamMemberResponse.json.
    """

    team_member: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        team_member = self.team_member.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "team_member": team_member,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User

        d = dict(src_dict)
        team_member = User.from_dict(d.pop("team_member"))

        schema = d.pop("$schema", UNSET)

        remove_team_member_response = cls(
            team_member=team_member,
            schema=schema,
        )

        return remove_team_member_response
