from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Feature")


@_attrs_define
class Feature:
    """
    Attributes:
        code (str):
        name (str):
        type_ (str):
        value (int):
    """

    code: str
    name: str
    type_: str
    value: int

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        name = self.name

        type_ = self.type_

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "code": code,
                "name": name,
                "type": type_,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        name = d.pop("name")

        type_ = d.pop("type")

        value = d.pop("value")

        feature = cls(
            code=code,
            name=name,
            type_=type_,
            value=value,
        )

        return feature
