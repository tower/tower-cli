import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.exported_catalog_property import ExportedCatalogProperty


T = TypeVar("T", bound="ExportedCatalog")


@_attrs_define
class ExportedCatalog:
    """
    Attributes:
        created_at (datetime.datetime):
        environment (str):
        name (str):
        properties (list['ExportedCatalogProperty']):
        type_ (str):
        slug (Union[Unset, str]): This property is deprecated. Please use name instead.
    """

    created_at: datetime.datetime
    environment: str
    name: str
    properties: list["ExportedCatalogProperty"]
    type_: str
    slug: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        environment = self.environment

        name = self.name

        properties = []
        for properties_item_data in self.properties:
            properties_item = properties_item_data.to_dict()
            properties.append(properties_item)

        type_ = self.type_

        slug = self.slug

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "CreatedAt": created_at,
                "environment": environment,
                "name": name,
                "properties": properties,
                "type": type_,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.exported_catalog_property import ExportedCatalogProperty

        d = dict(src_dict)
        created_at = isoparse(d.pop("CreatedAt"))

        environment = d.pop("environment")

        name = d.pop("name")

        properties = []
        _properties = d.pop("properties")
        for properties_item_data in _properties:
            properties_item = ExportedCatalogProperty.from_dict(properties_item_data)

            properties.append(properties_item)

        type_ = d.pop("type")

        slug = d.pop("slug", UNSET)

        exported_catalog = cls(
            created_at=created_at,
            environment=environment,
            name=name,
            properties=properties,
            type_=type_,
            slug=slug,
        )

        return exported_catalog
