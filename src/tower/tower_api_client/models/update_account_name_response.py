from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.account import Account


T = TypeVar("T", bound="UpdateAccountNameResponse")


@_attrs_define
class UpdateAccountNameResponse:
    """
    Attributes:
        account (Account):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAccountNameResponse.json.
    """

    account: "Account"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        account = self.account.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "account": account,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.account import Account

        d = dict(src_dict)
        account = Account.from_dict(d.pop("account"))

        schema = d.pop("$schema", UNSET)

        update_account_name_response = cls(
            account=account,
            schema=schema,
        )

        return update_account_name_response
