from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAppParams")


@_attrs_define
class CreateAppParams:
    """
    Attributes:
        name (str): The name of the app.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAppParams.json.
        is_externally_accessible (bool | Unset): Indicates that web traffic should be routed to this app and that its
            runs should get a hostname assigned to it. Default: False.
        short_description (str | Unset): A description of the app.
        slug (str | Unset): The slug of the app. Legacy CLI will send it but we don't need it.
        subdomain (None | str | Unset): The subdomain this app is accessible under. Requires is_externally_accessible to
            be true.
    """

    name: str
    schema: str | Unset = UNSET
    is_externally_accessible: bool | Unset = False
    short_description: str | Unset = UNSET
    slug: str | Unset = UNSET
    subdomain: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        is_externally_accessible = self.is_externally_accessible

        short_description = self.short_description

        slug = self.slug

        subdomain: None | str | Unset
        if isinstance(self.subdomain, Unset):
            subdomain = UNSET
        else:
            subdomain = self.subdomain

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
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        is_externally_accessible = d.pop("is_externally_accessible", UNSET)

        short_description = d.pop("short_description", UNSET)

        slug = d.pop("slug", UNSET)

        def _parse_subdomain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subdomain = _parse_subdomain(d.pop("subdomain", UNSET))

        create_app_params = cls(
            name=name,
            schema=schema,
            is_externally_accessible=is_externally_accessible,
            short_description=short_description,
            slug=slug,
            subdomain=subdomain,
        )

        return create_app_params
