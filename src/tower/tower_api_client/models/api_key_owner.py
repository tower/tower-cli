from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.api_key_owner_type import APIKeyOwnerType

T = TypeVar("T", bound="APIKeyOwner")


@_attrs_define
class APIKeyOwner:
    """
    Attributes:
        name (str): The owner's name: a user's full name (or email) or a service account's name.
        type_ (APIKeyOwnerType): The kind of principal this API key authenticates as.
    """

    name: str
    type_: APIKeyOwnerType

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

        type_ = APIKeyOwnerType(d.pop("type"))

        api_key_owner = cls(
            name=name,
            type_=type_,
        )

        return api_key_owner
