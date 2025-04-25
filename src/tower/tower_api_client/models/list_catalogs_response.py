from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog import Catalog
    from ..models.pagination import Pagination


T = TypeVar("T", bound="ListCatalogsResponse")


@_attrs_define
class ListCatalogsResponse:
    """
    Attributes:
        catalogs (list['Catalog']):
        pages (Pagination):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListCatalogsResponse.json.
    """

    catalogs: list["Catalog"]
    pages: "Pagination"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        catalogs = []
        for catalogs_item_data in self.catalogs:
            catalogs_item = catalogs_item_data.to_dict()
            catalogs.append(catalogs_item)

        pages = self.pages.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "catalogs": catalogs,
                "pages": pages,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog import Catalog
        from ..models.pagination import Pagination

        d = dict(src_dict)
        catalogs = []
        _catalogs = d.pop("catalogs")
        for catalogs_item_data in _catalogs:
            catalogs_item = Catalog.from_dict(catalogs_item_data)

            catalogs.append(catalogs_item)

        pages = Pagination.from_dict(d.pop("pages"))

        schema = d.pop("$schema", UNSET)

        list_catalogs_response = cls(
            catalogs=catalogs,
            pages=pages,
            schema=schema,
        )

        return list_catalogs_response
