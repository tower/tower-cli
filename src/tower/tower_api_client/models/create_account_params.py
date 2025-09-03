from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAccountParams")


@_attrs_define
class CreateAccountParams:
    """
    Attributes:
        email (str):
        password (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAccountParams.json.
    """

    email: str
    password: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        password = self.password

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "email": email,
                "password": password,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        password = d.pop("password")

        schema = d.pop("$schema", UNSET)

        create_account_params = cls(
            email=email,
            password=password,
            schema=schema,
        )

        return create_account_params
