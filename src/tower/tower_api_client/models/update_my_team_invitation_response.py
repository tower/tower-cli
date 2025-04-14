from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMyTeamInvitationResponse")


@attr.s(auto_attribs=True)
class UpdateMyTeamInvitationResponse:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateMyTeamInvitationResponse.json.
    """

    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        schema = d.pop("$schema", UNSET)

        update_my_team_invitation_response = cls(
            schema=schema,
        )

        return update_my_team_invitation_response
