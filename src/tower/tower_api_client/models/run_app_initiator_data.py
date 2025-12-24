from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.run_app_initiator_data_type import RunAppInitiatorDataType

T = TypeVar("T", bound="RunAppInitiatorData")


@_attrs_define
class RunAppInitiatorData:
    """
    Attributes:
        type_ (RunAppInitiatorDataType): The type of the initiator for this run.
    """

    type_: RunAppInitiatorDataType

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

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
        type_ = RunAppInitiatorDataType(d.pop("type"))

        run_app_initiator_data = cls(
            type_=type_,
        )

        return run_app_initiator_data
