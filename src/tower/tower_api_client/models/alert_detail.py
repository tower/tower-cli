from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="AlertDetail")


@_attrs_define
class AlertDetail:
    """
    Attributes:
        description (str):
        name (str):
    """

    description: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description")

        name = d.pop("name")

        alert_detail = cls(
            description=description,
            name=name,
        )

        return alert_detail
