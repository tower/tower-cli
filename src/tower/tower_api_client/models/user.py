import datetime
from typing import Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="User")


@attr.s(auto_attribs=True)
class User:
    """
    Attributes:
        company (str):
        country (str):
        created_at (datetime.datetime):
        email (str):
        first_name (str):
        is_invitation_claimed (bool):
        last_name (str):
        profile_photo_url (str):
    """

    company: str
    country: str
    created_at: datetime.datetime
    email: str
    first_name: str
    is_invitation_claimed: bool
    last_name: str
    profile_photo_url: str

    def to_dict(self) -> Dict[str, Any]:
        company = self.company
        country = self.country
        created_at = self.created_at.isoformat()

        email = self.email
        first_name = self.first_name
        is_invitation_claimed = self.is_invitation_claimed
        last_name = self.last_name
        profile_photo_url = self.profile_photo_url

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "company": company,
                "country": country,
                "created_at": created_at,
                "email": email,
                "first_name": first_name,
                "is_invitation_claimed": is_invitation_claimed,
                "last_name": last_name,
                "profile_photo_url": profile_photo_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        company = d.pop("company")

        country = d.pop("country")

        created_at = isoparse(d.pop("created_at"))

        email = d.pop("email")

        first_name = d.pop("first_name")

        is_invitation_claimed = d.pop("is_invitation_claimed")

        last_name = d.pop("last_name")

        profile_photo_url = d.pop("profile_photo_url")

        user = cls(
            company=company,
            country=country,
            created_at=created_at,
            email=email,
            first_name=first_name,
            is_invitation_claimed=is_invitation_claimed,
            last_name=last_name,
            profile_photo_url=profile_photo_url,
        )

        return user
