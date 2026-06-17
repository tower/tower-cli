from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.environment import Environment


T = TypeVar("T", bound="DescribeEnvironmentResponse")


@_attrs_define
class DescribeEnvironmentResponse:
    """
    Attributes:
        environment (Environment):
        number_catalogs (int):
        number_schedules (int):
        number_secrets (int):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeEnvironmentResponse.json.
    """

    environment: Environment
    number_catalogs: int
    number_schedules: int
    number_secrets: int
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment.to_dict()

        number_catalogs = self.number_catalogs

        number_schedules = self.number_schedules

        number_secrets = self.number_secrets

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environment": environment,
                "number_catalogs": number_catalogs,
                "number_schedules": number_schedules,
                "number_secrets": number_secrets,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.environment import Environment

        d = dict(src_dict)
        environment = Environment.from_dict(d.pop("environment"))

        number_catalogs = d.pop("number_catalogs")

        number_schedules = d.pop("number_schedules")

        number_secrets = d.pop("number_secrets")

        schema = d.pop("$schema", UNSET)

        describe_environment_response = cls(
            environment=environment,
            number_catalogs=number_catalogs,
            number_schedules=number_schedules,
            number_secrets=number_secrets,
            schema=schema,
        )

        return describe_environment_response
