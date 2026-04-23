from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="RegenerateGuestLoginURLResponse")


@_attrs_define
class RegenerateGuestLoginURLResponse:
    """
    Attributes:
        login_url (str): The new login URL to share with the guest.
        login_url_expires_at (datetime.datetime): When the login URL expires.
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/RegenerateGuestLoginURLResponse.json.
    """

    login_url: str
    login_url_expires_at: datetime.datetime
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        login_url = self.login_url

        login_url_expires_at = self.login_url_expires_at.isoformat()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "login_url": login_url,
                "login_url_expires_at": login_url_expires_at,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        login_url = d.pop("login_url")

        login_url_expires_at = isoparse(d.pop("login_url_expires_at"))

        schema = d.pop("$schema", UNSET)

        regenerate_guest_login_url_response = cls(
            login_url=login_url,
            login_url_expires_at=login_url_expires_at,
            schema=schema,
        )

        return regenerate_guest_login_url_response
