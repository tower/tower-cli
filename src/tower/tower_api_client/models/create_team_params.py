from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateTeamParams")


@attr.s(auto_attribs=True)
class CreateTeamParams:
    """
    Attributes:
        name (str): The name of the team to create
        slug (str): The slug of the team to create
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateTeamParams.json.
    """

    name: str
    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        slug = self.slug
        schema = self.schema

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
        name = d.pop("name")

        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        create_team_params = cls(
            name=name,
            slug=slug,
            schema=schema,
        )

        return create_team_params
