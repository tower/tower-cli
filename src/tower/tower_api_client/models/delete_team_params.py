from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteTeamParams")


@_attrs_define
class DeleteTeamParams:
    """
    Attributes:
        slug (str): The slug of the team to delete
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteTeamParams.json.
    """

    slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        slug = self.slug

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "slug": slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        slug = d.pop("slug")

        schema = d.pop("$schema", UNSET)

        delete_team_params = cls(
            slug=slug,
            schema=schema,
        )

        return delete_team_params
