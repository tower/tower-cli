from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSecretParams")


@attr.s(auto_attribs=True)
class CreateSecretParams:
    """
    Attributes:
        encrypted_value (str):
        environment (str):
        name (str):
        preview (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateSecretParams.json.
    """

    encrypted_value: str
    environment: str
    name: str
    preview: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        encrypted_value = self.encrypted_value
        environment = self.environment
        name = self.name
        preview = self.preview
        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        encrypted_value = d.pop("encrypted_value")

        environment = d.pop("environment")

        name = d.pop("name")

        preview = d.pop("preview")

        schema = d.pop("$schema", UNSET)

        create_secret_params = cls(
            encrypted_value=encrypted_value,
            environment=environment,
            name=name,
            preview=preview,
            schema=schema,
        )

        return create_secret_params
