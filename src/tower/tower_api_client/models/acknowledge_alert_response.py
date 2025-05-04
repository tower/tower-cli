from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AcknowledgeAlertResponse")


@_attrs_define
class AcknowledgeAlertResponse:
    """
    Attributes:
        status (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/AcknowledgeAlertResponse.json.
    """

    status: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "status": status,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        schema = d.pop("$schema", UNSET)

        acknowledge_alert_response = cls(
            status=status,
            schema=schema,
        )

        return acknowledge_alert_response
