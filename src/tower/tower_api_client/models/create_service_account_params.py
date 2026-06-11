from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.create_service_account_params_role import CreateServiceAccountParamsRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateServiceAccountParams")


@_attrs_define
class CreateServiceAccountParams:
    """
    Attributes:
        name (str): Human-readable name for the service account. Must be unique within the account.
        role (CreateServiceAccountParamsRole): The team role this service account acts as.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateServiceAccountParams.json.
        metadata (str | Unset): Optional, customer-supplied JSON metadata.
    """

    name: str
    role: CreateServiceAccountParamsRole
    schema: str | Unset = UNSET
    metadata: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        role = self.role.value

        schema = self.schema

        metadata = self.metadata

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "role": role,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        role = CreateServiceAccountParamsRole(d.pop("role"))

        schema = d.pop("$schema", UNSET)

        metadata = d.pop("metadata", UNSET)

        create_service_account_params = cls(
            name=name,
            role=role,
            schema=schema,
            metadata=metadata,
        )

        return create_service_account_params
