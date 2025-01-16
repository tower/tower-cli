from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetSecretsKeyOutputBody")


@_attrs_define
class GetSecretsKeyOutputBody:
    """
    Attributes:
        public_key (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        public_key = d.pop("public_key")

        schema = d.pop("$schema", UNSET)

        get_secrets_key_output_body = cls(
            public_key=public_key,
            schema=schema,
        )

        return get_secrets_key_output_body
