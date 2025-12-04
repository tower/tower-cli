from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunInitiator")


@_attrs_define
class RunInitiator:
    """
    Attributes:
        type_ (Union[None, str]): The type of initiator for this run
    """

    type_: Union[None, str]

    def to_dict(self) -> dict[str, Any]:
        type_: Union[None, str]
        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_type_(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        type_ = _parse_type_(d.pop("type"))

        run_initiator = cls(
            type_=type_,
        )

        return run_initiator
