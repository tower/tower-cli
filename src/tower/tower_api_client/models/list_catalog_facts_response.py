from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_fact import CatalogFact


T = TypeVar("T", bound="ListCatalogFactsResponse")


@_attrs_define
class ListCatalogFactsResponse:
    """
    Attributes:
        environment (str): Environment containing the catalog definition.
        facts (list[CatalogFact]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListCatalogFactsResponse.json.
    """

    environment: str
    facts: list[CatalogFact]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        facts = []
        for facts_item_data in self.facts:
            facts_item = facts_item_data.to_dict()
            facts.append(facts_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "environment": environment,
                "facts": facts,
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

        facts = []
        _facts = d.pop("facts")
        for facts_item_data in _facts:
            facts_item = CatalogFact.from_dict(facts_item_data)

            facts.append(facts_item)

        schema = d.pop("$schema", UNSET)

        list_catalog_facts_response = cls(
            environment=environment,
            facts=facts,
            schema=schema,
        )

        return list_catalog_facts_response
