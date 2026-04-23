from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CatalogProperty")


@_attrs_define
class CatalogProperty:
    """
    Attributes:
        name (str):
        preview (str):
        environment_variable (str | Unset): The environment variable name this property is injected as at runtime.
    """

    name: str
    preview: str
    environment_variable: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        preview = self.preview

        environment_variable = self.environment_variable

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "preview": preview,
            }
        )
        if environment_variable is not UNSET:
            field_dict["environment_variable"] = environment_variable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        preview = d.pop("preview")

        environment_variable = d.pop("environment_variable", UNSET)

        catalog_property = cls(
            name=name,
            preview=preview,
            environment_variable=environment_variable,
        )

        return catalog_property
