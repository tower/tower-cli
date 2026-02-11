from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="AuthenticationContext")


@_attrs_define
class AuthenticationContext:
    """
    Attributes:
        work_os_access_token (str): The WorkOS access token for SSO authentication.
    """

    work_os_access_token: str

    def to_dict(self) -> dict[str, Any]:
        work_os_access_token = self.work_os_access_token

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "work_os_access_token": work_os_access_token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        work_os_access_token = d.pop("work_os_access_token")

        authentication_context = cls(
            work_os_access_token=work_os_access_token,
        )

        return authentication_context
