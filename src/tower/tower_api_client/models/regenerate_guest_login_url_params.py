from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RegenerateGuestLoginURLParams")


@_attrs_define
class RegenerateGuestLoginURLParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/RegenerateGuestLoginURLParams.json.
        expires_in (int | Unset): The number of seconds the guest session should last. Defaults to 72 hours. Default:
            259200.
        redirect_url (str | Unset): Where to redirect the guest after they log in.
    """

    schema: str | Unset = UNSET
    expires_in: int | Unset = 259200
    redirect_url: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        expires_in = self.expires_in

        redirect_url = self.redirect_url

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if expires_in is not UNSET:
            field_dict["expires_in"] = expires_in
        if redirect_url is not UNSET:
            field_dict["redirect_url"] = redirect_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        expires_in = d.pop("expires_in", UNSET)

        redirect_url = d.pop("redirect_url", UNSET)

        regenerate_guest_login_url_params = cls(
            schema=schema,
            expires_in=expires_in,
            redirect_url=redirect_url,
        )

        return regenerate_guest_login_url_params
