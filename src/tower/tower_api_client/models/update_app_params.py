from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppParams")


@_attrs_define
class UpdateAppParams:
    """
    Attributes:
        description (str): New description for the App
        status (str): New status for the App
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppParams.json.
    """

    description: str
    status: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        status = self.status

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "status": status,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description")

        status = d.pop("status")

        schema = d.pop("$schema", UNSET)

        update_app_params = cls(
            description=description,
            status=status,
            schema=schema,
        )

        return update_app_params
