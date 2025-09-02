from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateEnvironmentParams")


@_attrs_define
class UpdateEnvironmentParams:
    """
    Attributes:
        new_name (str): The desired new name of the environment
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateEnvironmentParams.json.
    """

    new_name: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        new_name = self.new_name

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "new_name": new_name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_name = d.pop("new_name")

        schema = d.pop("$schema", UNSET)

        update_environment_params = cls(
            new_name=new_name,
            schema=schema,
        )

        return update_environment_params
