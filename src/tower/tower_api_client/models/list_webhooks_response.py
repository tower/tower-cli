from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.webhook import Webhook


T = TypeVar("T", bound="ListWebhooksResponse")


@_attrs_define
class ListWebhooksResponse:
    """
    Attributes:
        pages (Pagination):
        webhooks (list[Webhook]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListWebhooksResponse.json.
    """

    pages: Pagination
    webhooks: list[Webhook]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        webhooks = []
        for webhooks_item_data in self.webhooks:
            webhooks_item = webhooks_item_data.to_dict()
            webhooks.append(webhooks_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "pages": pages,
                "webhooks": webhooks,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.webhook import Webhook

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        webhooks = []
        _webhooks = d.pop("webhooks")
        for webhooks_item_data in _webhooks:
            webhooks_item = Webhook.from_dict(webhooks_item_data)

            webhooks.append(webhooks_item)

        schema = d.pop("$schema", UNSET)

        list_webhooks_response = cls(
            pages=pages,
            webhooks=webhooks,
            schema=schema,
        )

        return list_webhooks_response
