from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_service_account_params_role import UpdateServiceAccountParamsRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateServiceAccountParams")


@_attrs_define
class UpdateServiceAccountParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateServiceAccountParams.json.
        metadata (str | Unset): Replacement JSON metadata for the service account.
        name (str | Unset): The new human-readable name for the service account.
        role (UpdateServiceAccountParamsRole | Unset): The new team role this service account acts as.
    """

    schema: str | Unset = UNSET
    metadata: str | Unset = UNSET
    name: str | Unset = UNSET
    role: UpdateServiceAccountParamsRole | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        metadata = self.metadata

        name = self.name

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        metadata = d.pop("metadata", UNSET)

        name = d.pop("name", UNSET)

        _role = d.pop("role", UNSET)
        role: UpdateServiceAccountParamsRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = UpdateServiceAccountParamsRole(_role)

        update_service_account_params = cls(
            schema=schema,
            metadata=metadata,
            name=name,
            role=role,
        )

        return update_service_account_params
