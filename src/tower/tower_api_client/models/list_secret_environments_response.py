from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ListSecretEnvironmentsResponse")


@_attrs_define
class ListSecretEnvironmentsResponse:
    """
    Attributes:
        environments (list[str]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListSecretEnvironmentsResponse.json.
    """

    environments: list[str]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environments = self.environments

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environments": environments,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        environments = cast(list[str], d.pop("environments"))

        schema = d.pop("$schema", UNSET)

        list_secret_environments_response = cls(
            environments=environments,
            schema=schema,
        )

        return list_secret_environments_response
