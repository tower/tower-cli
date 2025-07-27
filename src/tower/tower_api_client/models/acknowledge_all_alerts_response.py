from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AcknowledgeAllAlertsResponse")


@_attrs_define
class AcknowledgeAllAlertsResponse:
    """
    Attributes:
        count (int): Number of alerts that were acknowledged
        status (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/AcknowledgeAllAlertsResponse.json.
    """

    count: int
    status: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        status = self.status

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "count": count,
                "status": status,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        count = d.pop("count")

        status = d.pop("status")

        schema = d.pop("$schema", UNSET)

        acknowledge_all_alerts_response = cls(
            count=count,
            status=status,
            schema=schema,
        )

        return acknowledge_all_alerts_response
