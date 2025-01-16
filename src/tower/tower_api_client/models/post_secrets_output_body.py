from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.secret import Secret


T = TypeVar("T", bound="PostSecretsOutputBody")


@_attrs_define
class PostSecretsOutputBody:
    """
    Attributes:
        secret (Secret):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.secret import Secret

        d = src_dict.copy()
        secret = Secret.from_dict(d.pop("secret"))

        schema = d.pop("$schema", UNSET)

        post_secrets_output_body = cls(
            secret=secret,
            schema=schema,
        )

        return post_secrets_output_body
