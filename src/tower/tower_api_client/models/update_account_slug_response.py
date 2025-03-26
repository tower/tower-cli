from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.account import Account


T = TypeVar("T", bound="UpdateAccountSlugResponse")


@attr.s(auto_attribs=True)
class UpdateAccountSlugResponse:
    """
    Attributes:
        account (Account):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateAccountSlugResponse.json.
    """

    account: "Account"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        account = self.account.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "account": account,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.account import Account

        d = src_dict.copy()
        account = Account.from_dict(d.pop("account"))

        schema = d.pop("$schema", UNSET)

        update_account_slug_response = cls(
            account=account,
            schema=schema,
        )

        return update_account_slug_response
