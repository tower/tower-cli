from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="CatalogUsage")


@_attrs_define
class CatalogUsage:
    """
    Attributes:
        measured_at (datetime.datetime | None): When this value was measured. Null when metering is unconfigured,
            disabled, or failed without a cached value.
        total_bytes (int): Physical bytes stored by this Tower-managed catalog, including Iceberg metadata and not-yet-
            compacted snapshot history.
    """

    measured_at: datetime.datetime | None
    total_bytes: int

    def to_dict(self) -> dict[str, Any]:
        measured_at: None | str
        if isinstance(self.measured_at, datetime.datetime):
            measured_at = self.measured_at.isoformat()
        else:
            measured_at = self.measured_at

        total_bytes = self.total_bytes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "measured_at": measured_at,
                "total_bytes": total_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_measured_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                measured_at_type_0 = isoparse(data)

                return measured_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        measured_at = _parse_measured_at(d.pop("measured_at"))

        total_bytes = d.pop("total_bytes")

        catalog_usage = cls(
            measured_at=measured_at,
            total_bytes=total_bytes,
        )

        return catalog_usage
