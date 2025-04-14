from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="CreateAccountParamsFlagsStruct")


@attr.s(auto_attribs=True)
class CreateAccountParamsFlagsStruct:
    """
    Attributes:
        is_test_account (bool):
    """

    is_test_account: bool

    def to_dict(self) -> Dict[str, Any]:
        is_test_account = self.is_test_account

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "is_test_account": is_test_account,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        is_test_account = d.pop("is_test_account")

        create_account_params_flags_struct = cls(
            is_test_account=is_test_account,
        )

        return create_account_params_flags_struct
