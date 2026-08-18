from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.catalog_fact_confidence import CatalogFactConfidence
from ..models.catalog_fact_scope import CatalogFactScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="CatalogFact")


@_attrs_define
class CatalogFact:
    """
    Attributes:
        confidence (CatalogFactConfidence): How trustworthy the fact is.
        created_at (datetime.datetime):
        name (str): The natural key of the fact within the catalog.
        object_ (str): Descriptive path to what the fact is about, e.g. "bronze.runs.deleted_at". Empty for catalog-
            scoped facts.
        scope (CatalogFactScope): What kind of object the fact is about.
        statement (str): The human-readable meaning of the fact.
        updated_at (datetime.datetime):
        body (Any | Unset): Optional structured payload (SQL, unit, enum values).
        source (str | Unset): Where the fact came from (agent id, user, ...).
    """

    confidence: CatalogFactConfidence
    created_at: datetime.datetime
    name: str
    object_: str
    scope: CatalogFactScope
    statement: str
    updated_at: datetime.datetime
    body: Any | Unset = UNSET
    source: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        confidence = self.confidence.value

        created_at = self.created_at.isoformat()

        name = self.name

        object_ = self.object_

        scope = self.scope.value

        statement = self.statement

        updated_at = self.updated_at.isoformat()

        body = self.body

        source = self.source

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "confidence": confidence,
                "created_at": created_at,
                "name": name,
                "object": object_,
                "scope": scope,
                "statement": statement,
                "updated_at": updated_at,
            }
        )
        if body is not UNSET:
            field_dict["body"] = body
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        confidence = CatalogFactConfidence(d.pop("confidence"))

        created_at = isoparse(d.pop("created_at"))

        name = d.pop("name")

        object_ = d.pop("object")

        scope = CatalogFactScope(d.pop("scope"))

        statement = d.pop("statement")

        updated_at = isoparse(d.pop("updated_at"))

        body = d.pop("body", UNSET)

        source = d.pop("source", UNSET)

        catalog_fact = cls(
            confidence=confidence,
            created_at=created_at,
            name=name,
            object_=object_,
            scope=scope,
            statement=statement,
            updated_at=updated_at,
            body=body,
            source=source,
        )

        return catalog_fact
