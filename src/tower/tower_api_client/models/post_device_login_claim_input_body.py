from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostDeviceLoginClaimInputBody")


@_attrs_define
class PostDeviceLoginClaimInputBody:
    """
    Attributes:
        user_code (str): The user code to claim.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    user_code: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user_code = self.user_code

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "user_code": user_code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_code = d.pop("user_code")

        schema = d.pop("$schema", UNSET)

        post_device_login_claim_input_body = cls(
            user_code=user_code,
            schema=schema,
        )

        return post_device_login_claim_input_body
