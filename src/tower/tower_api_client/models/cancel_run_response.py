from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="CancelRunResponse")


@_attrs_define
class CancelRunResponse:
    """
    Attributes:
        run (Run):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CancelRunResponse.json.
    """

    run: "Run"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        run = self.run.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "run": run,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run

        d = dict(src_dict)
        run = Run.from_dict(d.pop("run"))

        schema = d.pop("$schema", UNSET)

        cancel_run_response = cls(
            run=run,
            schema=schema,
        )

        return cancel_run_response
