from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.service_account import ServiceAccount


T = TypeVar("T", bound="ListServiceAccountsResponse")


@_attrs_define
class ListServiceAccountsResponse:
    """
    Attributes:
        pages (Pagination):
        service_accounts (list[ServiceAccount]):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListServiceAccountsResponse.json.
    """

    pages: Pagination
    service_accounts: list[ServiceAccount]
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        service_accounts = []
        for service_accounts_item_data in self.service_accounts:
            service_accounts_item = service_accounts_item_data.to_dict()
            service_accounts.append(service_accounts_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "pages": pages,
                "service_accounts": service_accounts,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.service_account import ServiceAccount

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        service_accounts = []
        _service_accounts = d.pop("service_accounts")
        for service_accounts_item_data in _service_accounts:
            service_accounts_item = ServiceAccount.from_dict(service_accounts_item_data)

            service_accounts.append(service_accounts_item)

        schema = d.pop("$schema", UNSET)

        list_service_accounts_response = cls(
            pages=pages,
            service_accounts=service_accounts,
            schema=schema,
        )

        return list_service_accounts_response
