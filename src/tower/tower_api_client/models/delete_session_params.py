from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteSessionParams")


@_attrs_define
class DeleteSessionParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DeleteSessionParams.json.
        session_id (str | Unset): The ID of the session to delete. If not provided, the current session will be deleted.
    """

    schema: str | Unset = UNSET
    session_id: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        session_id = self.session_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if session_id is not UNSET:
            field_dict["session_id"] = session_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        session_id = d.pop("session_id", UNSET)

        delete_session_params = cls(
            schema=schema,
            session_id=session_id,
        )

        return delete_session_params
