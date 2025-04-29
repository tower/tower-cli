from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RefreshSessionParams")


@_attrs_define
class RefreshSessionParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RefreshSessionParams.json.
    """

    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        refresh_session_params = cls(
            schema=schema,
        )

        return refresh_session_params
