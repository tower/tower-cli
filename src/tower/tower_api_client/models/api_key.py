from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_owner import APIKeyOwner


T = TypeVar("T", bound="APIKey")


@_attrs_define
class APIKey:
    """
    Attributes:
        created_at (datetime.datetime):
        identifier (str):
        last_used_at (datetime.datetime | None):
        name (str):
        expires_at (datetime.datetime | Unset):
        owner (APIKeyOwner | Unset):
        scopes (str | Unset):
    """

    created_at: datetime.datetime
    identifier: str
    last_used_at: datetime.datetime | None
    name: str
    expires_at: datetime.datetime | Unset = UNSET
    owner: APIKeyOwner | Unset = UNSET
    scopes: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        identifier = self.identifier

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        name = self.name

        expires_at: str | Unset = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        owner: dict[str, Any] | Unset = UNSET
        if not isinstance(self.owner, Unset):
            owner = self.owner.to_dict()

        scopes = self.scopes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "identifier": identifier,
                "last_used_at": last_used_at,
                "name": name,
            }
        )
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if owner is not UNSET:
            field_dict["owner"] = owner
        if scopes is not UNSET:
            field_dict["scopes"] = scopes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_owner import APIKeyOwner

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        identifier = d.pop("identifier")

        def _parse_last_used_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = isoparse(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

        name = d.pop("name")

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        _owner = d.pop("owner", UNSET)
        owner: APIKeyOwner | Unset
        if isinstance(_owner, Unset):
            owner = UNSET
        else:
            owner = APIKeyOwner.from_dict(_owner)

        scopes = d.pop("scopes", UNSET)

        api_key = cls(
            created_at=created_at,
            identifier=identifier,
            last_used_at=last_used_at,
            name=name,
            expires_at=expires_at,
            owner=owner,
            scopes=scopes,
        )

        return api_key
