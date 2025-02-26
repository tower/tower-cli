from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="SeriesPoint")


@attr.s(auto_attribs=True)
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

    def to_dict(self) -> Dict[str, Any]:
        failed = self.failed
        key = self.key
        successful = self.successful

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "failed": failed,
                "key": key,
                "successful": successful,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        failed = d.pop("failed")

        key = d.pop("key")

        successful = d.pop("successful")

        series_point = cls(
            failed=failed,
            key=key,
            successful=successful,
        )

        return series_point
