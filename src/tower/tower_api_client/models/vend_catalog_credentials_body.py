from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.vend_catalog_credentials_body_mode import VendCatalogCredentialsBodyMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="VendCatalogCredentialsBody")


@_attrs_define
class VendCatalogCredentialsBody:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/VendCatalogCredentialsBody.json.
        mode (VendCatalogCredentialsBodyMode | Unset): Access level for the vended token. "read" (default) binds the
            token to the catalog's read-only principal; "read-write" requires the catalogs:data:write scope and binds it to
            the read-write principal. Default: VendCatalogCredentialsBodyMode.READ.
    """

    schema: str | Unset = UNSET
    mode: VendCatalogCredentialsBodyMode | Unset = VendCatalogCredentialsBodyMode.READ

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        _mode = d.pop("mode", UNSET)
        mode: VendCatalogCredentialsBodyMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = VendCatalogCredentialsBodyMode(_mode)

        vend_catalog_credentials_body = cls(
            schema=schema,
            mode=mode,
        )

        return vend_catalog_credentials_body
