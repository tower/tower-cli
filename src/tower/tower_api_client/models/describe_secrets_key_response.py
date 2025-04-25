from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DescribeSecretsKeyResponse")


@_attrs_define
class DescribeSecretsKeyResponse:
    """
    Attributes:
        public_key (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeSecretsKeyResponse.json.
    """

    public_key: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        public_key = self.public_key

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "public_key": public_key,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        public_key = d.pop("public_key")

        schema = d.pop("$schema", UNSET)

        describe_secrets_key_response = cls(
            public_key=public_key,
            schema=schema,
        )

        return describe_secrets_key_response
