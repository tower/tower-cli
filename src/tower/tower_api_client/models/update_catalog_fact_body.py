from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_catalog_fact_body_confidence import UpdateCatalogFactBodyConfidence
from ..models.update_catalog_fact_body_scope import UpdateCatalogFactBodyScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateCatalogFactBody")


@_attrs_define
class UpdateCatalogFactBody:
    """
    Attributes:
        confidence (UpdateCatalogFactBodyConfidence): How trustworthy the fact is.
        scope (UpdateCatalogFactBodyScope): What kind of object the fact is about.
        statement (str): The human-readable meaning of the fact.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateCatalogFactBody.json.
        body (str | Unset): Optional structured payload (SQL, unit, enum values) as a JSON string.
        object_ (str | Unset): Descriptive path to what the fact is about, e.g. "bronze.runs.deleted_at". Empty for
            catalog-scoped facts.
        source (str | Unset): Where the fact came from (agent id, user, ...).
    """

    confidence: UpdateCatalogFactBodyConfidence
    scope: UpdateCatalogFactBodyScope
    statement: str
    schema: str | Unset = UNSET
    body: str | Unset = UNSET
    object_: str | Unset = UNSET
    source: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        confidence = self.confidence.value

        scope = self.scope.value

        statement = self.statement

        schema = self.schema

        body = self.body

        object_ = self.object_

        source = self.source

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "confidence": confidence,
                "scope": scope,
                "statement": statement,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if body is not UNSET:
            field_dict["body"] = body
        if object_ is not UNSET:
            field_dict["object"] = object_
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        confidence = UpdateCatalogFactBodyConfidence(d.pop("confidence"))

        scope = UpdateCatalogFactBodyScope(d.pop("scope"))

        statement = d.pop("statement")

        schema = d.pop("$schema", UNSET)

        body = d.pop("body", UNSET)

        object_ = d.pop("object", UNSET)

        source = d.pop("source", UNSET)

        update_catalog_fact_body = cls(
            confidence=confidence,
            scope=scope,
            statement=statement,
            schema=schema,
            body=body,
            object_=object_,
            source=source,
        )

        return update_catalog_fact_body
