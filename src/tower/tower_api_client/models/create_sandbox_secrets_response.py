from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSandboxSecretsResponse")


@_attrs_define
class CreateSandboxSecretsResponse:
    """
    Attributes:
        created (list[str]): List of secret keys that were created
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateSandboxSecretsResponse.json.
    """

    created: list[str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        created = self.created

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created": created,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created = cast(list[str], d.pop("created"))

        schema = d.pop("$schema", UNSET)

        create_sandbox_secrets_response = cls(
            created=created,
            schema=schema,
        )

        return create_sandbox_secrets_response
