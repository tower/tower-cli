from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostSecretsInputBody")


@_attrs_define
class PostSecretsInputBody:
    """
    Attributes:
        encrypted_value (str):
        environment (str):
        name (str):
        preview (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    encrypted_value: str
    environment: str
    name: str
    preview: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        encrypted_value = self.encrypted_value

        environment = self.environment

        name = self.name

        preview = self.preview

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "encrypted_value": encrypted_value,
                "environment": environment,
                "name": name,
                "preview": preview,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        encrypted_value = d.pop("encrypted_value")

        environment = d.pop("environment")

        name = d.pop("name")

        preview = d.pop("preview")

        schema = d.pop("$schema", UNSET)

        post_secrets_input_body = cls(
            encrypted_value=encrypted_value,
            environment=environment,
            name=name,
            preview=preview,
            schema=schema,
        )

        return post_secrets_input_body
