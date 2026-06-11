from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.service_account_role import ServiceAccountRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_account_creator import ServiceAccountCreator


T = TypeVar("T", bound="ServiceAccount")


@_attrs_define
class ServiceAccount:
    """
    Attributes:
        created_at (datetime.datetime): When the service account was created.
        id (str): The unique identifier for the service account.
        name (str): The human-readable name of the service account.
        role (ServiceAccountRole): The team role this service account acts as.
        updated_at (datetime.datetime): When the service account was last updated.
        creator (ServiceAccountCreator | Unset):
        metadata (Any | Unset): Customer-supplied JSON metadata associated with the service account.
    """

    created_at: datetime.datetime
    id: str
    name: str
    role: ServiceAccountRole
    updated_at: datetime.datetime
    creator: ServiceAccountCreator | Unset = UNSET
    metadata: Any | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        id = self.id

        name = self.name

        role = self.role.value

        updated_at = self.updated_at.isoformat()

        creator: dict[str, Any] | Unset = UNSET
        if not isinstance(self.creator, Unset):
            creator = self.creator.to_dict()

        metadata = self.metadata

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "id": id,
                "name": name,
                "role": role,
                "updated_at": updated_at,
            }
        )
        if creator is not UNSET:
            field_dict["creator"] = creator
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_account_creator import ServiceAccountCreator

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id")

        name = d.pop("name")

        role = ServiceAccountRole(d.pop("role"))

        updated_at = isoparse(d.pop("updated_at"))

        _creator = d.pop("creator", UNSET)
        creator: ServiceAccountCreator | Unset
        if isinstance(_creator, Unset):
            creator = UNSET
        else:
            creator = ServiceAccountCreator.from_dict(_creator)

        metadata = d.pop("metadata", UNSET)

        service_account = cls(
            created_at=created_at,
            id=id,
            name=name,
            role=role,
            updated_at=updated_at,
            creator=creator,
            metadata=metadata,
        )

        return service_account
