from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_membership import TeamMembership


T = TypeVar("T", bound="UpdateTeamMemberResponse")


@_attrs_define
class UpdateTeamMemberResponse:
    """
    Attributes:
        team_member (TeamMembership):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateTeamMemberResponse.json.
    """

    team_member: TeamMembership
    schema: str | Unset = UNSET

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
        from ..models.team_membership import TeamMembership

        d = dict(src_dict)
        team_member = TeamMembership.from_dict(d.pop("team_member"))

        schema = d.pop("$schema", UNSET)

        update_team_member_response = cls(
            team_member=team_member,
            schema=schema,
        )

        return update_team_member_response
