from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateAccountParamsFlagsStruct")


@_attrs_define
class CreateAccountParamsFlagsStruct:
    """
    Attributes:
        is_test_account (bool):
    """

    is_test_account: bool

    def to_dict(self) -> dict[str, Any]:
        is_test_account = self.is_test_account

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "is_test_account": is_test_account,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_test_account = d.pop("is_test_account")

        create_account_params_flags_struct = cls(
            is_test_account=is_test_account,
        )

        return create_account_params_flags_struct
