from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMyTeamInvitationResponse")


@_attrs_define
class UpdateMyTeamInvitationResponse:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateMyTeamInvitationResponse.json.
    """

    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        update_my_team_invitation_response = cls(
            schema=schema,
        )

        return update_my_team_invitation_response
