from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DescribeSecretsKeyResponse")


@attr.s(auto_attribs=True)
class DescribeSecretsKeyResponse:
    """
    Attributes:
        public_key (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DescribeSecretsKeyResponse.json.
    """

    public_key: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        public_key = self.public_key
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "public_key": public_key,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        public_key = d.pop("public_key")

        schema = d.pop("$schema", UNSET)

        describe_secrets_key_response = cls(
            public_key=public_key,
            schema=schema,
        )

        return describe_secrets_key_response
