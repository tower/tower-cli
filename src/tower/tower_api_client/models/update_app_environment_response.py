from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppEnvironmentResponse")


@_attrs_define
class UpdateAppEnvironmentResponse:
    """
    Attributes:
        environment (str):
        version (str):
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/UpdateAppEnvironmentResponse.json.
    """

    environment: str
    version: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        version = self.version

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environment": environment,
                "version": version,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        environment = d.pop("environment")

        version = d.pop("version")

        schema = d.pop("$schema", UNSET)

        update_app_environment_response = cls(
            environment=environment,
            version=version,
            schema=schema,
        )

        return update_app_environment_response
