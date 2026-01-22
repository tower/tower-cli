from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_team_member_params_role import UpdateTeamMemberParamsRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateTeamMemberParams")


@_attrs_define
class UpdateTeamMemberParams:
    """
    Attributes:
        email (str): The email address of the team member to update
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateTeamMemberParams.json.
        role (UpdateTeamMemberParamsRole | Unset): The role to update the team member to
    """

    email: str
    schema: str | Unset = UNSET
    role: UpdateTeamMemberParamsRole | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        schema = self.schema

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        schema = d.pop("$schema", UNSET)

        _role = d.pop("role", UNSET)
        role: UpdateTeamMemberParamsRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = UpdateTeamMemberParamsRole(_role)

        update_team_member_params = cls(
            email=email,
            schema=schema,
            role=role,
        )

        return update_team_member_params
