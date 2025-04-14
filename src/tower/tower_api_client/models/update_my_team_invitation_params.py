from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMyTeamInvitationParams")


@attr.s(auto_attribs=True)
class UpdateMyTeamInvitationParams:
    """
    Attributes:
        accepted (bool): Whether or not the invitation was accepted. If false, it's considered rejected.
        slug (str): The slug of the team invitation to update
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateMyTeamInvitationParams.json.
    """

    accepted: bool
    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        accepted = self.accepted
        slug = self.slug
        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        accepted = d.pop("accepted")

        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        update_my_team_invitation_params = cls(
            accepted=accepted,
            slug=slug,
            schema=schema,
        )

        return update_my_team_invitation_params
