from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="DescribeWhoamiResponse")


@_attrs_define
class DescribeWhoamiResponse:
    """
    Attributes:
        expires_at (datetime.datetime): Absolute time at which the token expires.
        token (str): RS256-signed identity JWT scoped to the authenticated user. Verify against the public keys at
            /.well-known/jwks.json.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeWhoamiResponse.json.
    """

    expires_at: datetime.datetime
    token: str
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        expires_at = self.expires_at.isoformat()

        token = self.token

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expires_at": expires_at,
                "token": token,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        expires_at = isoparse(d.pop("expires_at"))

        token = d.pop("token")

        schema = d.pop("$schema", UNSET)

        describe_whoami_response = cls(
            expires_at=expires_at,
            token=token,
            schema=schema,
        )

        return describe_whoami_response
