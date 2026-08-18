from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.tag_filter_op import TagFilterOp
from ..types import UNSET, Unset

T = TypeVar("T", bound="TagFilter")


@_attrs_define
class TagFilter:
    """
    Attributes:
        name (str): The tag name to search.
        op (TagFilterOp):
        value (str | Unset): Required if operator is eq
        values (list[str] | Unset): Required if operator is in or notIn
    """

    name: str
    op: TagFilterOp
    value: str | Unset = UNSET
    values: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        op = self.op.value

        value = self.value

        values: list[str] | Unset = UNSET
        if not isinstance(self.values, Unset):
            values = self.values

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "op": op,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        op = TagFilterOp(d.pop("op"))

        value = d.pop("value", UNSET)

        values = cast(list[str], d.pop("values", UNSET))

        tag_filter = cls(
            name=name,
            op=op,
            value=value,
            values=values,
        )

        return tag_filter
