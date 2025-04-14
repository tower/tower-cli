from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSessionParams")


@attr.s(auto_attribs=True)
class CreateSessionParams:
    """
    Attributes:
        password (str):
        username (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateSessionParams.json.
    """

    password: str
    username: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        password = self.password
        username = self.username
        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        password = d.pop("password")

        username = d.pop("username")

        schema = d.pop("$schema", UNSET)

        create_session_params = cls(
            password=password,
            username=username,
            schema=schema,
        )

        return create_session_params
