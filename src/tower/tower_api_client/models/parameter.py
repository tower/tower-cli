from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="Parameter")


@attr.s(auto_attribs=True)
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

    def to_dict(self) -> Dict[str, Any]:
        default = self.default
        description = self.description
        name = self.name

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "default": default,
                "description": description,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        default = d.pop("default")

        description = d.pop("description")

        name = d.pop("name")

        parameter = cls(
            default=default,
            description=description,
            name=name,
        )

        return parameter
