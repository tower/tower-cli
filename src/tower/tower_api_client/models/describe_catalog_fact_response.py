from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_fact import CatalogFact


T = TypeVar("T", bound="DescribeCatalogFactResponse")


@_attrs_define
class DescribeCatalogFactResponse:
    """
    Attributes:
        environment (str): Environment containing the catalog definition.
        fact (CatalogFact):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeCatalogFactResponse.json.
    """

    environment: str
    fact: CatalogFact
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        fact = self.fact.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environment": environment,
                "fact": fact,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_fact import CatalogFact

        d = dict(src_dict)
        environment = d.pop("environment")

        fact = CatalogFact.from_dict(d.pop("fact"))

        schema = d.pop("$schema", UNSET)

        describe_catalog_fact_response = cls(
            environment=environment,
            fact=fact,
            schema=schema,
        )

        return describe_catalog_fact_response
