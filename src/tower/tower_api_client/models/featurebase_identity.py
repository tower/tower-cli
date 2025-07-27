from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="FeaturebaseIdentity")


@_attrs_define
class FeaturebaseIdentity:
    """
    Attributes:
        company_hash (str):
        user_hash (str):
    """

    company_hash: str
    user_hash: str

    def to_dict(self) -> dict[str, Any]:
        company_hash = self.company_hash

        user_hash = self.user_hash

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "company_hash": company_hash,
                "user_hash": user_hash,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        company_hash = d.pop("company_hash")

        user_hash = d.pop("user_hash")

        featurebase_identity = cls(
            company_hash=company_hash,
            user_hash=user_hash,
        )

        return featurebase_identity
