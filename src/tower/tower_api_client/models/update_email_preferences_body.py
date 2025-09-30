from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.email_subscriptions import EmailSubscriptions


T = TypeVar("T", bound="UpdateEmailPreferencesBody")


@_attrs_define
class UpdateEmailPreferencesBody:
    """
    Attributes:
        subscriptions (EmailSubscriptions):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateEmailPreferencesBody.json.
    """

    subscriptions: "EmailSubscriptions"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        subscriptions = self.subscriptions.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "subscriptions": subscriptions,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.email_subscriptions import EmailSubscriptions

        d = dict(src_dict)
        subscriptions = EmailSubscriptions.from_dict(d.pop("subscriptions"))

        schema = d.pop("$schema", UNSET)

        update_email_preferences_body = cls(
            subscriptions=subscriptions,
            schema=schema,
        )

        return update_email_preferences_body
