from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="VerifyEmailParams")


@_attrs_define
class VerifyEmailParams:
    """
    Attributes:
        code (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/VerifyEmailParams.json.
    """

    code: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "code": code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        schema = d.pop("$schema", UNSET)

        verify_email_params = cls(
            code=code,
            schema=schema,
        )

        return verify_email_params
