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
        is_externally_accessible (Union[Unset, bool]): Indicates that web traffic should be routed to this app and that
            its runs should get a hostname assigned to it. Default: False.
        short_description (Union[Unset, str]): A description of the app.
        slug (Union[Unset, str]): The slug of the app. Legacy CLI will send it but we don't need it.
    """

    name: str
    schema: Union[Unset, str] = UNSET
    is_externally_accessible: Union[Unset, bool] = False
    short_description: Union[Unset, str] = UNSET
    slug: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        is_externally_accessible = self.is_externally_accessible

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
        if is_externally_accessible is not UNSET:
            field_dict["is_externally_accessible"] = is_externally_accessible
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

        is_externally_accessible = d.pop("is_externally_accessible", UNSET)

        short_description = d.pop("short_description", UNSET)

        slug = d.pop("slug", UNSET)

        create_app_params = cls(
            name=name,
            schema=schema,
            is_externally_accessible=is_externally_accessible,
            short_description=short_description,
            slug=slug,
        )

        return create_app_params
