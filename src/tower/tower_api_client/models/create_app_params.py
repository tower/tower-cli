from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAppParams")


@attr.s(auto_attribs=True)
class CreateAppParams:
    """
    Attributes:
        name (str): The name of the app.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateAppParams.json.
        short_description (Union[Unset, str]): A description of the app.
    """

    name: str
    schema: Union[Unset, str] = UNSET
    short_description: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        schema = self.schema
        short_description = self.short_description

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if short_description is not UNSET:
            field_dict["short_description"] = short_description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        short_description = d.pop("short_description", UNSET)

        create_app_params = cls(
            name=name,
            schema=schema,
            short_description=short_description,
        )

        return create_app_params
