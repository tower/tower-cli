from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.schedule_owner_type import ScheduleOwnerType

T = TypeVar("T", bound="ScheduleOwner")


@_attrs_define
class ScheduleOwner:
    """
    Attributes:
        name (str): The owner's name: a user's full name (first + last) or a service account's name. Must identify
            exactly one member of the account.
        type_ (ScheduleOwnerType): The kind of owner: 'user' or 'service_account'
    """

    name: str
    type_: ScheduleOwnerType

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

        type_ = ScheduleOwnerType(d.pop("type"))

        schedule_owner = cls(
            name=name,
            type_=type_,
        )

        return schedule_owner
