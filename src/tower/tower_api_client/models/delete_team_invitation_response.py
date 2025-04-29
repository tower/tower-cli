from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.team_invitation import TeamInvitation


T = TypeVar("T", bound="DeleteTeamInvitationResponse")


@_attrs_define
class DeleteTeamInvitationResponse:
    """
    Attributes:
        invitation (TeamInvitation):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteTeamInvitationResponse.json.
    """

    invitation: "TeamInvitation"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        invitation = self.invitation.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "invitation": invitation,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.team_invitation import TeamInvitation

        d = dict(src_dict)
        invitation = TeamInvitation.from_dict(d.pop("invitation"))

        schema = d.pop("$schema", UNSET)

        delete_team_invitation_response = cls(
            invitation=invitation,
            schema=schema,
        )

        return delete_team_invitation_response
