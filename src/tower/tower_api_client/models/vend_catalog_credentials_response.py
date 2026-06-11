from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_credentials import CatalogCredentials


T = TypeVar("T", bound="VendCatalogCredentialsResponse")


@_attrs_define
class VendCatalogCredentialsResponse:
    """
    Attributes:
        credentials (CatalogCredentials):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/VendCatalogCredentialsResponse.json.
    """

    credentials: CatalogCredentials
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        credentials = self.credentials.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "credentials": credentials,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_credentials import CatalogCredentials

        d = dict(src_dict)
        credentials = CatalogCredentials.from_dict(d.pop("credentials"))

        schema = d.pop("$schema", UNSET)

        vend_catalog_credentials_response = cls(
            credentials=credentials,
            schema=schema,
        )

        return vend_catalog_credentials_response
