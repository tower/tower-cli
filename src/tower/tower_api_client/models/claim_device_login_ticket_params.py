from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimDeviceLoginTicketParams")


@_attrs_define
class ClaimDeviceLoginTicketParams:
    """
    Attributes:
        refresh_token (str): The refresh token for the session to delegate to the device.
        user_code (str): The user code to claim.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ClaimDeviceLoginTicketParams.json.
    """

    refresh_token: str
    user_code: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        refresh_token = self.refresh_token

        user_code = self.user_code

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "refresh_token": refresh_token,
                "user_code": user_code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        refresh_token = d.pop("refresh_token")

        user_code = d.pop("user_code")

        schema = d.pop("$schema", UNSET)

        claim_device_login_ticket_params = cls(
            refresh_token=refresh_token,
            user_code=user_code,
            schema=schema,
        )

        return claim_device_login_ticket_params
