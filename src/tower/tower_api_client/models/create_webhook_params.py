from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateWebhookParams")


@_attrs_define
class CreateWebhookParams:
    """
    Attributes:
        name (str): The name of the webhook.
        url (str): The webhook URL.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateWebhookParams.json.
    """

    name: str
    url: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        url = self.url

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "url": url,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        url = d.pop("url")

        schema = d.pop("$schema", UNSET)

        create_webhook_params = cls(
            name=name,
            url=url,
            schema=schema,
        )

        return create_webhook_params
