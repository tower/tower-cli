from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="SeriesPoint")


@_attrs_define
class SeriesPoint:
    """
    Attributes:
        failed (int):
        key (str):
        successful (int):
    """

    failed: int
    key: str
    successful: int

    def to_dict(self) -> dict[str, Any]:
        failed = self.failed

        key = self.key

        successful = self.successful

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "failed": failed,
                "key": key,
                "successful": successful,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        failed = d.pop("failed")

        key = d.pop("key")

        successful = d.pop("successful")

        series_point = cls(
            failed=failed,
            key=key,
            successful=successful,
        )

        return series_point
