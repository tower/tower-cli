from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_log_line import RunLogLine


T = TypeVar("T", bound="BatchedRunLogLines")


@_attrs_define
class BatchedRunLogLines:
    """
    Attributes:
        error (None | str | Unset):
        log_lines (list[RunLogLine] | Unset):
    """

    error: None | str | Unset = UNSET
    log_lines: list[RunLogLine] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        log_lines: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.log_lines, Unset):
            log_lines = []
            for log_lines_item_data in self.log_lines:
                log_lines_item = log_lines_item_data.to_dict()
                log_lines.append(log_lines_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error
        if log_lines is not UNSET:
            field_dict["log_lines"] = log_lines

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_log_line import RunLogLine

        d = dict(src_dict)

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        _log_lines = d.pop("log_lines", UNSET)
        log_lines: list[RunLogLine] | Unset = UNSET
        if _log_lines is not UNSET:
            log_lines = []
            for log_lines_item_data in _log_lines:
                log_lines_item = RunLogLine.from_dict(log_lines_item_data)

                log_lines.append(log_lines_item)

        batched_run_log_lines = cls(
            error=error,
            log_lines=log_lines,
        )

        return batched_run_log_lines
