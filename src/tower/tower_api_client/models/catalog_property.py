from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CatalogProperty")


@_attrs_define
class CatalogProperty:
    """
    Attributes:
        name (str):
        preview (str):
    """

    name: str
    preview: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        preview = self.preview

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
                "preview": preview,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        preview = d.pop("preview")

        catalog_property = cls(
            name=name,
            preview=preview,
        )

        return catalog_property
