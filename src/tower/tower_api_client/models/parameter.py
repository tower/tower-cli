from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Parameter")


@_attrs_define
class Parameter:
    """
    Attributes:
        default (str):
        description (str):
        name (str):
    """

    default: str
    description: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        default = self.default

        description = self.description

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "default": default,
                "description": description,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        default = d.pop("default")

        description = d.pop("description")

        name = d.pop("name")

        parameter = cls(
            default=default,
            description=description,
            name=name,
        )

        return parameter
