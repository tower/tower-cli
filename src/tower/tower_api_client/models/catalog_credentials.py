from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="CatalogCredentials")


@_attrs_define
class CatalogCredentials:
    """
    Attributes:
        catalog_uri (str): The Iceberg REST catalog endpoint.
        expires_at (datetime.datetime): When the OAuth token expires.
        mode (str): Access level the token is bound to.
        oauth_token (str): Short-lived OAuth bearer token.
        warehouse (str): The Polaris catalog identifier (REST prefix).
    """

    catalog_uri: str
    expires_at: datetime.datetime
    mode: str
    oauth_token: str
    warehouse: str

    def to_dict(self) -> dict[str, Any]:
        catalog_uri = self.catalog_uri

        expires_at = self.expires_at.isoformat()

        mode = self.mode

        oauth_token = self.oauth_token

        warehouse = self.warehouse

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "catalog_uri": catalog_uri,
                "expires_at": expires_at,
                "mode": mode,
                "oauth_token": oauth_token,
                "warehouse": warehouse,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        catalog_uri = d.pop("catalog_uri")

        expires_at = isoparse(d.pop("expires_at"))

        mode = d.pop("mode")

        oauth_token = d.pop("oauth_token")

        warehouse = d.pop("warehouse")

        catalog_credentials = cls(
            catalog_uri=catalog_uri,
            expires_at=expires_at,
            mode=mode,
            oauth_token=oauth_token,
            warehouse=warehouse,
        )

        return catalog_credentials
