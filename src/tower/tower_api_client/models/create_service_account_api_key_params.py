from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateServiceAccountAPIKeyParams")


@_attrs_define
class CreateServiceAccountAPIKeyParams:
    """
    Attributes:
        name (str): Human-readable name for the API key.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateServiceAccountAPIKeyParams.json.
        expires_at (datetime.datetime | Unset): When the API key expires.
        scopes (str | Unset): Space-separated scopes for the key. Defaults to the SA's role scopes when omitted.
    """

    name: str
    schema: str | Unset = UNSET
    expires_at: datetime.datetime | Unset = UNSET
    scopes: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        expires_at: str | Unset = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        scopes = self.scopes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if scopes is not UNSET:
            field_dict["scopes"] = scopes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        scopes = d.pop("scopes", UNSET)

        create_service_account_api_key_params = cls(
            name=name,
            schema=schema,
            expires_at=expires_at,
            scopes=scopes,
        )

        return create_service_account_api_key_params
