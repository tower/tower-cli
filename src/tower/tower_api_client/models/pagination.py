from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Pagination")


@_attrs_define
class Pagination:
    """
    Attributes:
        num_pages (int):
        page (int):
        page_size (int):
        total (int):
    """

    num_pages: int
    page: int
    page_size: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        num_pages = self.num_pages

        page = self.page

        page_size = self.page_size

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "num_pages": num_pages,
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        num_pages = d.pop("num_pages")

        page = d.pop("page")

        page_size = d.pop("page_size")

        total = d.pop("total")

        pagination = cls(
            num_pages=num_pages,
            page=page,
            page_size=page_size,
            total=total,
        )

        return pagination
