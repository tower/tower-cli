from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostSessionInputBody")


@_attrs_define
class PostSessionInputBody:
    """
    Attributes:
        password (str):
        username (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    password: str
    username: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        password = self.password

        username = self.username

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "password": password,
                "username": username,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        password = d.pop("password")

        username = d.pop("username")

        schema = d.pop("$schema", UNSET)

        post_session_input_body = cls(
            password=password,
            username=username,
            schema=schema,
        )

        return post_session_input_body
