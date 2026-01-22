from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook import Webhook


T = TypeVar("T", bound="CreateWebhookResponse")


@_attrs_define
class CreateWebhookResponse:
    """
    Attributes:
        signing_key (str):
        webhook (Webhook):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateWebhookResponse.json.
    """

    signing_key: str
    webhook: Webhook
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        signing_key = self.signing_key

        webhook = self.webhook.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "signing_key": signing_key,
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
        signing_key = d.pop("signing_key")

        webhook = Webhook.from_dict(d.pop("webhook"))

        schema = d.pop("$schema", UNSET)

        create_webhook_response = cls(
            signing_key=signing_key,
            webhook=webhook,
            schema=schema,
        )

        return create_webhook_response
