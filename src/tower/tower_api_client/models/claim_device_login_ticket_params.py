from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClaimDeviceLoginTicketParams")


@attr.s(auto_attribs=True)
class ClaimDeviceLoginTicketParams:
    """
    Attributes:
        user_code (str): The user code to claim.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ClaimDeviceLoginTicketParams.json.
    """

    user_code: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        user_code = self.user_code
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "user_code": user_code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        user_code = d.pop("user_code")

        schema = d.pop("$schema", UNSET)

        claim_device_login_ticket_params = cls(
            user_code=user_code,
            schema=schema,
        )

        return claim_device_login_ticket_params
