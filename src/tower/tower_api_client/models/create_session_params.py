from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSessionParams")


@_attrs_define
class CreateSessionParams:
    """
    Attributes:
        password (str):
        username (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateSessionParams.json.
        code (Union[Unset, str]): One-time password verification code for two-factor authentication. If the user has
            two-factor authentication enabled, this code is required to log in.
    """

    password: str
    username: str
    schema: Union[Unset, str] = UNSET
    code: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        password = self.password

        username = self.username

        schema = self.schema

        code = self.code

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "password": password,
                "username": username,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if code is not UNSET:
            field_dict["code"] = code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        password = d.pop("password")

        username = d.pop("username")

        schema = d.pop("$schema", UNSET)

        code = d.pop("code", UNSET)

        create_session_params = cls(
            password=password,
            username=username,
            schema=schema,
            code=code,
        )

        return create_session_params
