from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.catalog import Catalog


T = TypeVar("T", bound="UpdateCatalogResponse")


@_attrs_define
class UpdateCatalogResponse:
    """
    Attributes:
        catalog (Catalog):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateCatalogResponse.json.
    """

    catalog: "Catalog"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        catalog = self.catalog.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "catalog": catalog,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog import Catalog

        d = dict(src_dict)
        catalog = Catalog.from_dict(d.pop("catalog"))

        schema = d.pop("$schema", UNSET)

        update_catalog_response = cls(
            catalog=catalog,
            schema=schema,
        )

        return update_catalog_response
