import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDeviceLoginTicketResponse")


@_attrs_define
class CreateDeviceLoginTicketResponse:
    """
    Attributes:
        device_code (str): The unique code identifying this device login request.
        expires_in (int): Number of seconds until this request expires.
        generated_at (datetime.datetime): When this device login request was created.
        interval (int): Number of seconds to wait between polling attempts.
        login_url (str): The URL where the user should go to enter the user code.
        user_code (str): The code that the user needs to enter to authenticate.
        verification_url (str): The URL that the device should poll to check authentication status.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateDeviceLoginTicketResponse.json.
    """

    device_code: str
    expires_in: int
    generated_at: datetime.datetime
    interval: int
    login_url: str
    user_code: str
    verification_url: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        device_code = self.device_code

        expires_in = self.expires_in

        generated_at = self.generated_at.isoformat()

        interval = self.interval

        login_url = self.login_url

        user_code = self.user_code

        verification_url = self.verification_url

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "device_code": device_code,
                "expires_in": expires_in,
                "generated_at": generated_at,
                "interval": interval,
                "login_url": login_url,
                "user_code": user_code,
                "verification_url": verification_url,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device_code = d.pop("device_code")

        expires_in = d.pop("expires_in")

        generated_at = isoparse(d.pop("generated_at"))

        interval = d.pop("interval")

        login_url = d.pop("login_url")

        user_code = d.pop("user_code")

        verification_url = d.pop("verification_url")

        schema = d.pop("$schema", UNSET)

        create_device_login_ticket_response = cls(
            device_code=device_code,
            expires_in=expires_in,
            generated_at=generated_at,
            interval=interval,
            login_url=login_url,
            user_code=user_code,
            verification_url=verification_url,
            schema=schema,
        )

        return create_device_login_ticket_response
