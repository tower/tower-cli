from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteTeamParams")


@attr.s(auto_attribs=True)
class DeleteTeamParams:
    """
    Attributes:
        slug (str): The slug of the team to delete
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DeleteTeamParams.json.
    """

    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        slug = self.slug
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "slug": slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        delete_team_params = cls(
            slug=slug,
            schema=schema,
        )

        return delete_team_params
