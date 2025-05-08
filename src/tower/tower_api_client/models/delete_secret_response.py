from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.secret import Secret


T = TypeVar("T", bound="DeleteSecretResponse")


@_attrs_define
class DeleteSecretResponse:
    """
    Attributes:
        secret (Secret):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteSecretResponse.json.
    """

    secret: "Secret"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        secret = self.secret.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "secret": secret,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.secret import Secret

        d = dict(src_dict)
        secret = Secret.from_dict(d.pop("secret"))

        schema = d.pop("$schema", UNSET)

        delete_secret_response = cls(
            secret=secret,
            schema=schema,
        )

        return delete_secret_response
