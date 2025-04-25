from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateTeamParams")


@_attrs_define
class CreateTeamParams:
    """
    Attributes:
        name (str): The name of the team to create
        slug (str): The slug of the team to create
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateTeamParams.json.
    """

    name: str
    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        schema = self.schema

        field_dict: dict[str, Any] = {}
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        create_team_params = cls(
            name=name,
            slug=slug,
            schema=schema,
        )

        return create_team_params
