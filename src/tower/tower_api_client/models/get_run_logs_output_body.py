from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_run_log_line import GetRunLogLine


T = TypeVar("T", bound="GetRunLogsOutputBody")


@attr.s(auto_attribs=True)
class GetRunLogsOutputBody:
    """
    Attributes:
        log_lines (List['GetRunLogLine']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/GetRunLogsOutputBody.json.
    """

    log_lines: List["GetRunLogLine"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        log_lines = []
        for log_lines_item_data in self.log_lines:
            log_lines_item = log_lines_item_data.to_dict()

            log_lines.append(log_lines_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "log_lines": log_lines,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_run_log_line import GetRunLogLine

        d = src_dict.copy()
        log_lines = []
        _log_lines = d.pop("log_lines")
        for log_lines_item_data in _log_lines:
            log_lines_item = GetRunLogLine.from_dict(log_lines_item_data)

            log_lines.append(log_lines_item)

        schema = d.pop("$schema", UNSET)

        get_run_logs_output_body = cls(
            log_lines=log_lines,
            schema=schema,
        )

        return get_run_logs_output_body
