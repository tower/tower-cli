import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="VerifiedAuthenticator")


@_attrs_define
class VerifiedAuthenticator:
    """
    Attributes:
        created_at (datetime.datetime): The ISO8601 timestamp indicating when this authenticator was created
        id (str): The ID of this authenticator
        issuer (str): The issuer of the unverified authenticator.
        label (str): The label that is used for this unverified authenticator.
    """

    created_at: datetime.datetime
    id: str
    issuer: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        id = self.id

        issuer = self.issuer

        label = self.label

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "id": id,
                "issuer": issuer,
                "label": label,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id")

        issuer = d.pop("issuer")

        label = d.pop("label")

        verified_authenticator = cls(
            created_at=created_at,
            id=id,
            issuer=issuer,
            label=label,
        )

        return verified_authenticator
