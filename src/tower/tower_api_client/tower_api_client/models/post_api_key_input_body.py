from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostAPIKeyInputBody")


@_attrs_define
class PostAPIKeyInputBody:
    """
    Attributes:
        name (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    name: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        post_api_key_input_body = cls(
            name=name,
            schema=schema,
        )

        return post_api_key_input_body
