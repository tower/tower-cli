from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_log_line import RunLogLine


T = TypeVar("T", bound="DescribeRunLogsResponse")


@_attrs_define
class DescribeRunLogsResponse:
    """
    Attributes:
        log_lines (list['RunLogLine']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeRunLogsResponse.json.
    """

    log_lines: list["RunLogLine"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        log_lines = []
        for log_lines_item_data in self.log_lines:
            log_lines_item = log_lines_item_data.to_dict()
            log_lines.append(log_lines_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "log_lines": log_lines,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_log_line import RunLogLine

        d = dict(src_dict)
        log_lines = []
        _log_lines = d.pop("log_lines")
        for log_lines_item_data in _log_lines:
            log_lines_item = RunLogLine.from_dict(log_lines_item_data)

            log_lines.append(log_lines_item)

        schema = d.pop("$schema", UNSET)

        describe_run_logs_response = cls(
            log_lines=log_lines,
            schema=schema,
        )

        return describe_run_logs_response
