from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.parameter import Parameter


T = TypeVar("T", bound="AppVersion")


@_attrs_define
class AppVersion:
    """
    Attributes:
        created_at (datetime.datetime):
        parameters (list[Parameter]):
        towerfile (str): The Towerfile that this version was created from.
        version (str):
        content_checksum (str | Unset): Server-computed SHA256 of the bundle contents for this version.
        idempotency_key (str | Unset): Client-supplied key (e.g. git SHA) that produced this version, or empty if none
            was supplied at deploy time.
    """

    created_at: datetime.datetime
    parameters: list[Parameter]
    towerfile: str
    version: str
    content_checksum: str | Unset = UNSET
    idempotency_key: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        parameters = []
        for parameters_item_data in self.parameters:
            parameters_item = parameters_item_data.to_dict()
            parameters.append(parameters_item)

        towerfile = self.towerfile

        version = self.version

        content_checksum = self.content_checksum

        idempotency_key = self.idempotency_key

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "created_at": created_at,
                "parameters": parameters,
                "towerfile": towerfile,
                "version": version,
            }
        )
        if content_checksum is not UNSET:
            field_dict["content_checksum"] = content_checksum
        if idempotency_key is not UNSET:
            field_dict["idempotency_key"] = idempotency_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.parameter import Parameter

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        parameters = []
        _parameters = d.pop("parameters")
        for parameters_item_data in _parameters:
            parameters_item = Parameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        towerfile = d.pop("towerfile")

        version = d.pop("version")

        content_checksum = d.pop("content_checksum", UNSET)

        idempotency_key = d.pop("idempotency_key", UNSET)

        app_version = cls(
            created_at=created_at,
            parameters=parameters,
            towerfile=towerfile,
            version=version,
            content_checksum=content_checksum,
            idempotency_key=idempotency_key,
        )

        return app_version
