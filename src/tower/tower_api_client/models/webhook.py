from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.webhook_state import WebhookState
from ..types import UNSET, Unset

T = TypeVar("T", bound="Webhook")


@_attrs_define
class Webhook:
    """
    Attributes:
        account_id (str):
        created_at (datetime.datetime):
        created_by_id (str):
        last_checked_at (datetime.datetime | None):
        name (str):
        state (WebhookState):
        url (str):
        deleted_at (datetime.datetime | Unset):
    """

    account_id: str
    created_at: datetime.datetime
    created_by_id: str
    last_checked_at: datetime.datetime | None
    name: str
    state: WebhookState
    url: str
    deleted_at: datetime.datetime | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        account_id = self.account_id

        created_at = self.created_at.isoformat()

        created_by_id = self.created_by_id

        last_checked_at: None | str
        if isinstance(self.last_checked_at, datetime.datetime):
            last_checked_at = self.last_checked_at.isoformat()
        else:
            last_checked_at = self.last_checked_at

        name = self.name

        state = self.state.value

        url = self.url

        deleted_at: str | Unset = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "account_id": account_id,
                "created_at": created_at,
                "created_by_id": created_by_id,
                "last_checked_at": last_checked_at,
                "name": name,
                "state": state,
                "url": url,
            }
        )
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_id = d.pop("account_id")

        created_at = isoparse(d.pop("created_at"))

        created_by_id = d.pop("created_by_id")

        def _parse_last_checked_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_checked_at_type_0 = isoparse(data)

                return last_checked_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_checked_at = _parse_last_checked_at(d.pop("last_checked_at"))

        name = d.pop("name")

        state = WebhookState(d.pop("state"))

        url = d.pop("url")

        _deleted_at = d.pop("deleted_at", UNSET)
        deleted_at: datetime.datetime | Unset
        if isinstance(_deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)

        webhook = cls(
            account_id=account_id,
            created_at=created_at,
            created_by_id=created_by_id,
            last_checked_at=last_checked_at,
            name=name,
            state=state,
            url=url,
            deleted_at=deleted_at,
        )

        return webhook
