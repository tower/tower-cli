from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimDeviceLoginTicketParams")


@_attrs_define
class ClaimDeviceLoginTicketParams:
    """
    Attributes:
        user_code (str): The user code to claim.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ClaimDeviceLoginTicketParams.json.
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_code = d.pop("user_code")

        schema = d.pop("$schema", UNSET)

        claim_device_login_ticket_params = cls(
            user_code=user_code,
            schema=schema,
        )

        return claim_device_login_ticket_params
