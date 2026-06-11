from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.run_creator_type import RunCreatorType

T = TypeVar("T", bound="RunCreator")


@_attrs_define
class RunCreator:
    """
    Attributes:
        name (str): The creator's name: a user's full name (or email) or a service account's name.
        type_ (RunCreatorType): The kind of principal that created the run.
    """

    name: str
    type_: RunCreatorType

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        type_ = RunCreatorType(d.pop("type"))

        run_creator = cls(
            name=name,
            type_=type_,
        )

        return run_creator
