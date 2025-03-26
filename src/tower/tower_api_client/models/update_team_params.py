from typing import Any, Dict, Optional, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateTeamParams")


@attr.s(auto_attribs=True)
class UpdateTeamParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateTeamParams.json.
        name (Optional[str]): The name of the team to create. This is optional, if you supply null it will not update
            the team name.
        slug (Optional[str]): The new slug that you want the team to use. This is optional, if you supply null it will
            not update the slug.
    """

    name: Optional[str]
    slug: Optional[str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        schema = self.schema
        name = self.name
        slug = self.slug

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "slug": slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        schema = d.pop("$schema", UNSET)

        name = d.pop("name")

        slug = d.pop("slug")

        update_team_params = cls(
            schema=schema,
            name=name,
            slug=slug,
        )

        return update_team_params
