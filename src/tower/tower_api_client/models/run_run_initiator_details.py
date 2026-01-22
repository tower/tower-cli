from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunRunInitiatorDetails")


@_attrs_define
class RunRunInitiatorDetails:
    """
    Attributes:
        run_app_name (str | Unset): The name of the app that initiated this run, if type is 'tower_run'
        run_number (int | Unset): The number of the run that initaited this run, if type is 'tower_run'
    """

    run_app_name: str | Unset = UNSET
    run_number: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        run_app_name = self.run_app_name

        run_number = self.run_number

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if run_app_name is not UNSET:
            field_dict["run_app_name"] = run_app_name
        if run_number is not UNSET:
            field_dict["run_number"] = run_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        run_app_name = d.pop("run_app_name", UNSET)

        run_number = d.pop("run_number", UNSET)

        run_run_initiator_details = cls(
            run_app_name=run_app_name,
            run_number=run_number,
        )

        return run_run_initiator_details
