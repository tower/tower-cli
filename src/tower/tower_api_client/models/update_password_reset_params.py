from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatePasswordResetParams")


@_attrs_define
class UpdatePasswordResetParams:
    """
    Attributes:
        password (str): The new password that you want to set for your account
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdatePasswordResetParams.json.
    """

    password: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        password = self.password

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "password": password,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        password = d.pop("password")

        schema = d.pop("$schema", UNSET)

        update_password_reset_params = cls(
            password=password,
            schema=schema,
        )

        return update_password_reset_params
