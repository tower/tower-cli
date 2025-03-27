from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.secret import Secret


T = TypeVar("T", bound="CreateSecretResponse")


@attr.s(auto_attribs=True)
class CreateSecretResponse:
    """
    Attributes:
        secret (Secret):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateSecretResponse.json.
    """

    secret: "Secret"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        secret = self.secret.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "secret": secret,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.secret import Secret

        d = src_dict.copy()
        secret = Secret.from_dict(d.pop("secret"))

        schema = d.pop("$schema", UNSET)

        create_secret_response = cls(
            secret=secret,
            schema=schema,
        )

        return create_secret_response
