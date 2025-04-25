import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        company (str):
        country (str):
        created_at (datetime.datetime):
        email (str):
        first_name (str):
        is_alerts_enabled (bool):
        is_invitation_claimed (bool):
        last_name (str):
        profile_photo_url (str):
    """

    company: str
    country: str
    created_at: datetime.datetime
    email: str
    first_name: str
    is_alerts_enabled: bool
    is_invitation_claimed: bool
    last_name: str
    profile_photo_url: str

    def to_dict(self) -> dict[str, Any]:
        company = self.company

        country = self.country

        created_at = self.created_at.isoformat()

        email = self.email

        first_name = self.first_name

        is_alerts_enabled = self.is_alerts_enabled

        is_invitation_claimed = self.is_invitation_claimed

        last_name = self.last_name

        profile_photo_url = self.profile_photo_url

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "company": company,
                "country": country,
                "created_at": created_at,
                "email": email,
                "first_name": first_name,
                "is_alerts_enabled": is_alerts_enabled,
                "is_invitation_claimed": is_invitation_claimed,
                "last_name": last_name,
                "profile_photo_url": profile_photo_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        company = d.pop("company")

        country = d.pop("country")

        created_at = isoparse(d.pop("created_at"))

        email = d.pop("email")

        first_name = d.pop("first_name")

        is_alerts_enabled = d.pop("is_alerts_enabled")

        is_invitation_claimed = d.pop("is_invitation_claimed")

        last_name = d.pop("last_name")

        profile_photo_url = d.pop("profile_photo_url")

        user = cls(
            company=company,
            country=country,
            created_at=created_at,
            email=email,
            first_name=first_name,
            is_alerts_enabled=is_alerts_enabled,
            is_invitation_claimed=is_invitation_claimed,
            last_name=last_name,
            profile_photo_url=profile_photo_url,
        )

        return user
