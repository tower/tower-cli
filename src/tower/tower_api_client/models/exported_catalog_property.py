from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ExportedCatalogProperty")


@_attrs_define
class ExportedCatalogProperty:
    """
    Attributes:
        encrypted_value (str):
        name (str):
        preview (str):
    """

    encrypted_value: str
    name: str
    preview: str

    def to_dict(self) -> dict[str, Any]:
        encrypted_value = self.encrypted_value

        name = self.name

        preview = self.preview

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "encrypted_value": encrypted_value,
                "name": name,
                "preview": preview,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        encrypted_value = d.pop("encrypted_value")

        name = d.pop("name")

        preview = d.pop("preview")

        exported_catalog_property = cls(
            encrypted_value=encrypted_value,
            name=name,
            preview=preview,
        )

        return exported_catalog_property
