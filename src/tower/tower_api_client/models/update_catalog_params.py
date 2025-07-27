from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.encrypted_catalog_property import EncryptedCatalogProperty


T = TypeVar("T", bound="UpdateCatalogParams")


@_attrs_define
class UpdateCatalogParams:
    """
    Attributes:
        environment (str): New environment for the catalog
        properties (list['EncryptedCatalogProperty']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateCatalogParams.json.
    """

    environment: str
    properties: list["EncryptedCatalogProperty"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        properties = []
        for properties_item_data in self.properties:
            properties_item = properties_item_data.to_dict()
            properties.append(properties_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
                "properties": properties,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.encrypted_catalog_property import EncryptedCatalogProperty

        d = dict(src_dict)
        environment = d.pop("environment")

        properties = []
        _properties = d.pop("properties")
        for properties_item_data in _properties:
            properties_item = EncryptedCatalogProperty.from_dict(properties_item_data)

            properties.append(properties_item)

        schema = d.pop("$schema", UNSET)

        update_catalog_params = cls(
            environment=environment,
            properties=properties,
            schema=schema,
        )

        return update_catalog_params
