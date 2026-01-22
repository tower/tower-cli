from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.run_run_initiator_details import RunRunInitiatorDetails
    from ..models.schedule_run_initiator_details import ScheduleRunInitiatorDetails


T = TypeVar("T", bound="RunInitiator")


@_attrs_define
class RunInitiator:
    """
    Attributes:
        details (RunRunInitiatorDetails | ScheduleRunInitiatorDetails): Additional information about the initiator of a
            run.
        type_ (None | str): The type of initiator for this run. Null if none or unknown.
    """

    details: RunRunInitiatorDetails | ScheduleRunInitiatorDetails
    type_: None | str

    def to_dict(self) -> dict[str, Any]:
        from ..models.schedule_run_initiator_details import ScheduleRunInitiatorDetails

        details: dict[str, Any]
        if isinstance(self.details, ScheduleRunInitiatorDetails):
            details = self.details.to_dict()
        else:
            details = self.details.to_dict()

        type_: None | str
        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "details": details,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_run_initiator_details import RunRunInitiatorDetails
        from ..models.schedule_run_initiator_details import ScheduleRunInitiatorDetails

        d = dict(src_dict)

        def _parse_details(
            data: object,
        ) -> RunRunInitiatorDetails | ScheduleRunInitiatorDetails:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                details_type_0 = ScheduleRunInitiatorDetails.from_dict(data)

                return details_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            details_type_1 = RunRunInitiatorDetails.from_dict(data)

            return details_type_1

        details = _parse_details(d.pop("details"))

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        run_initiator = cls(
            details=details,
            type_=type_,
        )

        return run_initiator
