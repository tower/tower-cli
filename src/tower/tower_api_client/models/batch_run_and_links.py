from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_error import BatchError
    from ..models.run_and_links import RunAndLinks


T = TypeVar("T", bound="BatchRunAndLinks")


@_attrs_define
class BatchRunAndLinks:
    """
    Attributes:
        data (RunAndLinks | Unset):
        error (BatchError | Unset):
    """

    data: RunAndLinks | Unset = UNSET
    error: BatchError | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_error import BatchError
        from ..models.run_and_links import RunAndLinks

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: RunAndLinks | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = RunAndLinks.from_dict(_data)

        _error = d.pop("error", UNSET)
        error: BatchError | Unset
        if isinstance(_error, Unset):
            error = UNSET
        else:
            error = BatchError.from_dict(_error)

        batch_run_and_links = cls(
            data=data,
            error=error,
        )

        return batch_run_and_links
