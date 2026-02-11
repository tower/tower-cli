from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Token")


@_attrs_define
class Token:
    """
    Attributes:
        access_token (str): The access token to use when authenticating API requests with Tower.
        jwt (str):
        refresh_token (str | Unset): The refresh token to use when refreshing an expired access token. For security
            reasons, refresh tokens should only be transmitted over secure channels and never logged or stored in plaintext.
            It will only be returned upon initial authentication or when explicitly refreshing the access token.
    """

    access_token: str
    jwt: str
    refresh_token: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        jwt = self.jwt

        refresh_token = self.refresh_token

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "access_token": access_token,
                "jwt": jwt,
            }
        )
        if refresh_token is not UNSET:
            field_dict["refresh_token"] = refresh_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("access_token")

        jwt = d.pop("jwt")

        refresh_token = d.pop("refresh_token", UNSET)

        token = cls(
            access_token=access_token,
            jwt=jwt,
            refresh_token=refresh_token,
        )

        return token
