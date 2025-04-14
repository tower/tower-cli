from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimDeviceLoginTicketResponse")


@attr.s(auto_attribs=True)
class ClaimDeviceLoginTicketResponse:
    """
    Attributes:
        claimed (bool): Whether the code was successfully claimed.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ClaimDeviceLoginTicketResponse.json.
    """

    claimed: bool
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        claimed = self.claimed
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "claimed": claimed,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        claimed = d.pop("claimed")

        schema = d.pop("$schema", UNSET)

        claim_device_login_ticket_response = cls(
            claimed=claimed,
            schema=schema,
        )

        return claim_device_login_ticket_response
