from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Guest")


@_attrs_define
class Guest:
    """
    Attributes:
        app (str): The name of the app this guest can access.
        created_at (datetime.datetime): When the guest was created.
        id (str): The unique identifier for the guest.
        name (str | Unset): Optional display name for the guest.
    """

    app: str
    created_at: datetime.datetime
    id: str
    name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        app = self.app

        created_at = self.created_at.isoformat()

        id = self.id

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "app": app,
                "created_at": created_at,
                "id": id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app = d.pop("app")

        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id")

        name = d.pop("name", UNSET)

        guest = cls(
            app=app,
            created_at=created_at,
            id=id,
            name=name,
        )

        return guest
