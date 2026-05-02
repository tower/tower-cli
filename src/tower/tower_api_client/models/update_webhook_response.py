from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook import Webhook


T = TypeVar("T", bound="UpdateWebhookResponse")


@_attrs_define
class UpdateWebhookResponse:
    """
    Attributes:
        webhook (Webhook):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateWebhookResponse.json.
    """

    webhook: Webhook
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        webhook = self.webhook.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "webhook": webhook,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook import Webhook

        d = dict(src_dict)
        webhook = Webhook.from_dict(d.pop("webhook"))

        schema = d.pop("$schema", UNSET)

        update_webhook_response = cls(
            webhook=webhook,
            schema=schema,
        )

        return update_webhook_response
