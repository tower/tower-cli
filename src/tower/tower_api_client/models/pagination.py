from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="Pagination")


@attr.s(auto_attribs=True)
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

    def to_dict(self) -> Dict[str, Any]:
        num_pages = self.num_pages
        page = self.page
        page_size = self.page_size
        total = self.total

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
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
