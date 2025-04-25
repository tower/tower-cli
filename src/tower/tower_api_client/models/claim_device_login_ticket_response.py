from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimDeviceLoginTicketResponse")


@_attrs_define
class ClaimDeviceLoginTicketResponse:
    """
    Attributes:
        claimed (bool): Whether the code was successfully claimed.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ClaimDeviceLoginTicketResponse.json.
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        claimed = d.pop("claimed")

        schema = d.pop("$schema", UNSET)

        claim_device_login_ticket_response = cls(
            claimed=claimed,
            schema=schema,
        )

        return claim_device_login_ticket_response
