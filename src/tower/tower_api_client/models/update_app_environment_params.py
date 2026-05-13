from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppEnvironmentParams")


@_attrs_define
class UpdateAppEnvironmentParams:
    """
    Attributes:
        version (str): The version to deploy to this environment, e.g. 'v1', 'v2'.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppEnvironmentParams.json.
    """

    version: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "version": version,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        version = d.pop("version")

        schema = d.pop("$schema", UNSET)

        update_app_environment_params = cls(
            version=version,
            schema=schema,
        )

        return update_app_environment_params
