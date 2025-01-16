from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostAppsInputBody")


@_attrs_define
class PostAppsInputBody:
    """
    Attributes:
        name (str): The name of the app.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
        short_description (Union[Unset, str]): A description of the app.
    """

    name: str
    schema: Union[Unset, str] = UNSET
    short_description: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        short_description = self.short_description

        field_dict: dict[str, Any] = {}
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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        short_description = d.pop("short_description", UNSET)

        post_apps_input_body = cls(
            name=name,
            schema=schema,
            short_description=short_description,
        )

        return post_apps_input_body
