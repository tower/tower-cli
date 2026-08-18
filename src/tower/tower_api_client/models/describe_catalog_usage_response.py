from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_usage import CatalogUsage


T = TypeVar("T", bound="DescribeCatalogUsageResponse")


@_attrs_define
class DescribeCatalogUsageResponse:
    """
    Attributes:
        environment (str): Environment containing the catalog definition.
        usage (CatalogUsage):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeCatalogUsageResponse.json.
    """

    environment: str
    usage: CatalogUsage
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        usage = self.usage.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environment": environment,
                "usage": usage,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_usage import CatalogUsage

        d = dict(src_dict)
        environment = d.pop("environment")

        usage = CatalogUsage.from_dict(d.pop("usage"))

        schema = d.pop("$schema", UNSET)

        describe_catalog_usage_response = cls(
            environment=environment,
            usage=usage,
            schema=schema,
        )

        return describe_catalog_usage_response
