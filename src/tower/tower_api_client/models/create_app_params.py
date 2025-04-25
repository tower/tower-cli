from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAppParams")


@_attrs_define
class CreateAppParams:
    """
    Attributes:
        name (str): The name of the app.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAppParams.json.
        short_description (Union[Unset, str]): A description of the app.
        slug (Union[Unset, str]): A slug for the app.
    """

    name: str
    schema: Union[Unset, str] = UNSET
    short_description: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        short_description = self.short_description

        slug = self.slug

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if short_description is not UNSET:
            field_dict["short_description"] = short_description
        if slug is not UNSET:
            field_dict["slug"] = slug

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        short_description = d.pop("short_description", UNSET)

        slug = d.pop("slug", UNSET)

        create_app_params = cls(
            name=name,
            schema=schema,
            short_description=short_description,
            slug=slug,
        )

        return create_app_params
