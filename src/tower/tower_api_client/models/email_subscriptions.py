from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailSubscriptions")


@_attrs_define
class EmailSubscriptions:
    """
    Attributes:
        feature_updates (Union[Unset, bool]):
        marketing_emails (Union[Unset, bool]):
        tower_newsletter (Union[Unset, bool]):
    """

    feature_updates: Union[Unset, bool] = UNSET
    marketing_emails: Union[Unset, bool] = UNSET
    tower_newsletter: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        feature_updates = self.feature_updates

        marketing_emails = self.marketing_emails

        tower_newsletter = self.tower_newsletter

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if feature_updates is not UNSET:
            field_dict["feature_updates"] = feature_updates
        if marketing_emails is not UNSET:
            field_dict["marketing_emails"] = marketing_emails
        if tower_newsletter is not UNSET:
            field_dict["tower_newsletter"] = tower_newsletter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        feature_updates = d.pop("feature_updates", UNSET)

        marketing_emails = d.pop("marketing_emails", UNSET)

        tower_newsletter = d.pop("tower_newsletter", UNSET)

        email_subscriptions = cls(
            feature_updates=feature_updates,
            marketing_emails=marketing_emails,
            tower_newsletter=tower_newsletter,
        )

        return email_subscriptions
