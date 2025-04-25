import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.catalog_property import CatalogProperty


T = TypeVar("T", bound="Catalog")


@_attrs_define
class Catalog:
    """
    Attributes:
        created_at (datetime.datetime):
        environment (str):
        name (str):
        properties (list['CatalogProperty']):
        slug (str):
        type_ (str):
    """

    created_at: datetime.datetime
    environment: str
    name: str
    properties: list["CatalogProperty"]
    slug: str
    type_: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        environment = self.environment

        name = self.name

        properties = []
        for properties_item_data in self.properties:
            properties_item = properties_item_data.to_dict()
            properties.append(properties_item)

        slug = self.slug

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "CreatedAt": created_at,
                "environment": environment,
                "name": name,
                "properties": properties,
                "slug": slug,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.catalog_property import CatalogProperty

        d = dict(src_dict)
        created_at = isoparse(d.pop("CreatedAt"))

        environment = d.pop("environment")

        name = d.pop("name")

        properties = []
        _properties = d.pop("properties")
        for properties_item_data in _properties:
            properties_item = CatalogProperty.from_dict(properties_item_data)

            properties.append(properties_item)

        slug = d.pop("slug")

        type_ = d.pop("type")

        catalog = cls(
            created_at=created_at,
            environment=environment,
            name=name,
            properties=properties,
            slug=slug,
            type_=type_,
        )

        return catalog
