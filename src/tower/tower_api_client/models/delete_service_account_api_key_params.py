from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteServiceAccountAPIKeyParams")


@_attrs_define
class DeleteServiceAccountAPIKeyParams:
    """
    Attributes:
        identifier (str): The API key identifier (with or without the 'sk-' prefix).
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteServiceAccountAPIKeyParams.json.
    """

    identifier: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "identifier": identifier,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identifier = d.pop("identifier")

        schema = d.pop("$schema", UNSET)

        delete_service_account_api_key_params = cls(
            identifier=identifier,
            schema=schema,
        )

        return delete_service_account_api_key_params
