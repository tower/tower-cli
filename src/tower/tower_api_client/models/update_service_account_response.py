from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_account import ServiceAccount


T = TypeVar("T", bound="UpdateServiceAccountResponse")


@_attrs_define
class UpdateServiceAccountResponse:
    """
    Attributes:
        service_account (ServiceAccount):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateServiceAccountResponse.json.
    """

    service_account: ServiceAccount
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        service_account = self.service_account.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "service_account": service_account,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_account import ServiceAccount

        d = dict(src_dict)
        service_account = ServiceAccount.from_dict(d.pop("service_account"))

        schema = d.pop("$schema", UNSET)

        update_service_account_response = cls(
            service_account=service_account,
            schema=schema,
        )

        return update_service_account_response
