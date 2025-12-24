from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunGraphRunID")


@_attrs_define
class RunGraphRunID:
    """
    Attributes:
        app_name (str):
        number (int):
    """

    app_name: str
    number: int

    def to_dict(self) -> dict[str, Any]:
        app_name = self.app_name

        number = self.number

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app_name": app_name,
                "number": number,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_name = d.pop("app_name")

        number = d.pop("number")

        run_graph_run_id = cls(
            app_name=app_name,
            number=number,
        )

        return run_graph_run_id
