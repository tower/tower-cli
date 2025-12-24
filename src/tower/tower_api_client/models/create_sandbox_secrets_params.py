from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSandboxSecretsParams")


@_attrs_define
class CreateSandboxSecretsParams:
    """
    Attributes:
        environment (str): Environment to create secrets in
        secret_keys (list[str]): List of secret keys to create with Tower defaults
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateSandboxSecretsParams.json.
    """

    environment: str
    secret_keys: list[str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        secret_keys = self.secret_keys

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
                "secret_keys": secret_keys,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        environment = d.pop("environment")

        secret_keys = cast(list[str], d.pop("secret_keys"))

        schema = d.pop("$schema", UNSET)

        create_sandbox_secrets_params = cls(
            environment=environment,
            secret_keys=secret_keys,
            schema=schema,
        )

        return create_sandbox_secrets_params
