from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateGuestParams")


@_attrs_define
class CreateGuestParams:
    """
    Attributes:
        app (str): The name of the externally accessible app this guest can access.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateGuestParams.json.
        expires_in (int | Unset): The number of seconds the guest session should last. Defaults to 72 hours. Default:
            259200.
        name (str | Unset): Optional display name for the guest.
        redirect_url (str | Unset): Where to redirect the guest after they log in. Defaults to the app's subdomain.
    """

    app: str
    schema: str | Unset = UNSET
    expires_in: int | Unset = 259200
    name: str | Unset = UNSET
    redirect_url: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        app = self.app

        schema = self.schema

        expires_in = self.expires_in

        name = self.name

        redirect_url = self.redirect_url

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "app": app,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if expires_in is not UNSET:
            field_dict["expires_in"] = expires_in
        if name is not UNSET:
            field_dict["name"] = name
        if redirect_url is not UNSET:
            field_dict["redirect_url"] = redirect_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app = d.pop("app")

        schema = d.pop("$schema", UNSET)

        expires_in = d.pop("expires_in", UNSET)

        name = d.pop("name", UNSET)

        redirect_url = d.pop("redirect_url", UNSET)

        create_guest_params = cls(
            app=app,
            schema=schema,
            expires_in=expires_in,
            name=name,
            redirect_url=redirect_url,
        )

        return create_guest_params
