from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog_fact import CatalogFact


T = TypeVar("T", bound="UpdateCatalogFactResponse")


@_attrs_define
class UpdateCatalogFactResponse:
    """
    Attributes:
        fact (CatalogFact):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateCatalogFactResponse.json.
    """

    fact: CatalogFact
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        fact = self.fact.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
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
        fact = CatalogFact.from_dict(d.pop("fact"))

        schema = d.pop("$schema", UNSET)

        update_catalog_fact_response = cls(
            fact=fact,
            schema=schema,
        )

        return update_catalog_fact_response
