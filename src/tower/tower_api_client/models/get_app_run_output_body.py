from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="GetAppRunOutputBody")


@_attrs_define
class GetAppRunOutputBody:
    """
    Attributes:
        run (Run):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.run import Run

        d = src_dict.copy()
        run = Run.from_dict(d.pop("run"))

        schema = d.pop("$schema", UNSET)

        get_app_run_output_body = cls(
            run=run,
            schema=schema,
        )

        return get_app_run_output_body
