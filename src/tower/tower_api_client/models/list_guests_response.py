from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guest import Guest


T = TypeVar("T", bound="ListGuestsResponse")


@_attrs_define
class ListGuestsResponse:
    """
    Attributes:
        guests (list[Guest]): List of guests.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListGuestsResponse.json.
    """

    guests: list[Guest]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        guests = []
        for guests_item_data in self.guests:
            guests_item = guests_item_data.to_dict()
            guests.append(guests_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "guests": guests,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.guest import Guest

        d = dict(src_dict)
        guests = []
        _guests = d.pop("guests")
        for guests_item_data in _guests:
            guests_item = Guest.from_dict(guests_item_data)

            guests.append(guests_item)

        schema = d.pop("$schema", UNSET)

        list_guests_response = cls(
            guests=guests,
            schema=schema,
        )

        return list_guests_response
