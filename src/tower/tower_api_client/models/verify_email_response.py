from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="VerifyEmailResponse")


@_attrs_define
class VerifyEmailResponse:
    """
    Attributes:
        user (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/VerifyEmailResponse.json.
    """

    user: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "user": user,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User

        d = dict(src_dict)
        user = User.from_dict(d.pop("user"))

        schema = d.pop("$schema", UNSET)

        verify_email_response = cls(
            user=user,
            schema=schema,
        )

        return verify_email_response
