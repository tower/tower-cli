from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.create_catalog_params_type import CreateCatalogParamsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.encrypted_catalog_property import EncryptedCatalogProperty


T = TypeVar("T", bound="CreateCatalogParams")


@_attrs_define
class CreateCatalogParams:
    """
    Attributes:
        environment (str):
        name (str):
        properties (list['EncryptedCatalogProperty']):
        type_ (CreateCatalogParamsType):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateCatalogParams.json.
    """

    environment: str
    name: str
    properties: list["EncryptedCatalogProperty"]
    type_: CreateCatalogParamsType
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        name = self.name

        properties = []
        for properties_item_data in self.properties:
            properties_item = properties_item_data.to_dict()
            properties.append(properties_item)

        type_ = self.type_.value

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
                "name": name,
                "properties": properties,
                "type": type_,
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

        name = d.pop("name")

        properties = []
        _properties = d.pop("properties")
        for properties_item_data in _properties:
            properties_item = EncryptedCatalogProperty.from_dict(properties_item_data)

            properties.append(properties_item)

        type_ = CreateCatalogParamsType(d.pop("type"))

        schema = d.pop("$schema", UNSET)

        create_catalog_params = cls(
            environment=environment,
            name=name,
            properties=properties,
            type_=type_,
            schema=schema,
        )

        return create_catalog_params
