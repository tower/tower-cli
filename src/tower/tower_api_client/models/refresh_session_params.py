from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RefreshSessionParams")


@_attrs_define
class RefreshSessionParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RefreshSessionParams.json.
        refresh_token (str | Unset): The refresh token associated with the session to refresh.
    """

    schema: str | Unset = UNSET
    refresh_token: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        refresh_token = self.refresh_token

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if refresh_token is not UNSET:
            field_dict["refresh_token"] = refresh_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        refresh_token = d.pop("refresh_token", UNSET)

        refresh_session_params = cls(
            schema=schema,
            refresh_token=refresh_token,
        )

        return refresh_session_params
