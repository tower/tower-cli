from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.authentication_context import AuthenticationContext


T = TypeVar("T", bound="DescribeAuthenticationContextBody")


@_attrs_define
class DescribeAuthenticationContextBody:
    """
    Attributes:
        authentication_context (AuthenticationContext):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeAuthenticationContextBody.json.
    """

    authentication_context: AuthenticationContext
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        authentication_context = self.authentication_context.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "authentication_context": authentication_context,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.authentication_context import AuthenticationContext

        d = dict(src_dict)
        authentication_context = AuthenticationContext.from_dict(
            d.pop("authentication_context")
        )

        schema = d.pop("$schema", UNSET)

        describe_authentication_context_body = cls(
            authentication_context=authentication_context,
            schema=schema,
        )

        return describe_authentication_context_body
