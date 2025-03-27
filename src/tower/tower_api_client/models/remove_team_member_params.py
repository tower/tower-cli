from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="RemoveTeamMemberParams")


@attr.s(auto_attribs=True)
class RemoveTeamMemberParams:
    """
    Attributes:
        email (str): The email address of the team member to remove
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/RemoveTeamMemberParams.json.
    """

    email: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        email = self.email
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "email": email,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        email = d.pop("email")

        schema = d.pop("$schema", UNSET)

        remove_team_member_params = cls(
            email=email,
            schema=schema,
        )

        return remove_team_member_params
