from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guest import Guest


T = TypeVar("T", bound="CreateGuestResponse")


@_attrs_define
class CreateGuestResponse:
    """
    Attributes:
        guest (Guest):
        login_url (str): The URL to share with the guest for logging in.
        login_url_expires_at (datetime.datetime): When the login URL expires.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateGuestResponse.json.
    """

    guest: Guest
    login_url: str
    login_url_expires_at: datetime.datetime
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        guest = self.guest.to_dict()

        login_url = self.login_url

        login_url_expires_at = self.login_url_expires_at.isoformat()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "guest": guest,
                "login_url": login_url,
                "login_url_expires_at": login_url_expires_at,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.guest import Guest

        d = dict(src_dict)
        guest = Guest.from_dict(d.pop("guest"))

        login_url = d.pop("login_url")

        login_url_expires_at = isoparse(d.pop("login_url_expires_at"))

        schema = d.pop("$schema", UNSET)

        create_guest_response = cls(
            guest=guest,
            login_url=login_url,
            login_url_expires_at=login_url_expires_at,
            schema=schema,
        )

        return create_guest_response
