from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UnverifiedAuthenticator")


@_attrs_define
class UnverifiedAuthenticator:
    """
    Attributes:
        issuer (str): The issuer of the unverified authenticator.
        key (str): The key of the unverified authenticator.
        label (str): The label that is used for this unverified authenticator.
        url (str): The full URL of the authenticator.
    """

    issuer: str
    key: str
    label: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        issuer = self.issuer

        key = self.key

        label = self.label

        url = self.url

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "issuer": issuer,
                "key": key,
                "label": label,
                "url": url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        issuer = d.pop("issuer")

        key = d.pop("key")

        label = d.pop("label")

        url = d.pop("url")

        unverified_authenticator = cls(
            issuer=issuer,
            key=key,
            label=label,
            url=url,
        )

        return unverified_authenticator
