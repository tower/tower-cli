from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreatePasswordResetResponse")


@_attrs_define
class CreatePasswordResetResponse:
    """
    Attributes:
        ok (bool): A boolean indicating the request was successfully processed.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreatePasswordResetResponse.json.
    """

    ok: bool
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        ok = self.ok

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "ok": ok,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ok = d.pop("ok")

        schema = d.pop("$schema", UNSET)

        create_password_reset_response = cls(
            ok=ok,
            schema=schema,
        )

        return create_password_reset_response
