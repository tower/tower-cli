from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostDeviceLoginClaimOutputBody")


@_attrs_define
class PostDeviceLoginClaimOutputBody:
    """
    Attributes:
        claimed (bool): Whether the code was successfully claimed.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    claimed: bool
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        claimed = self.claimed

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "claimed": claimed,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        claimed = d.pop("claimed")

        schema = d.pop("$schema", UNSET)

        post_device_login_claim_output_body = cls(
            claimed=claimed,
            schema=schema,
        )

        return post_device_login_claim_output_body
