from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMyTeamInvitationParams")


@_attrs_define
class UpdateMyTeamInvitationParams:
    """
    Attributes:
        accepted (bool): Whether or not the invitation was accepted. If false, it's considered rejected.
        slug (str): The slug of the team invitation to update
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateMyTeamInvitationParams.json.
    """

    accepted: bool
    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        accepted = self.accepted

        slug = self.slug

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "accepted": accepted,
                "slug": slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        accepted = d.pop("accepted")

        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        update_my_team_invitation_params = cls(
            accepted=accepted,
            slug=slug,
            schema=schema,
        )

        return update_my_team_invitation_params
