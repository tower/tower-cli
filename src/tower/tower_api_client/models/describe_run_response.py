from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run import Run


T = TypeVar("T", bound="DescribeRunResponse")


@attr.s(auto_attribs=True)
class DescribeRunResponse:
    """
    Attributes:
        run (Run):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DescribeRunResponse.json.
    """

    run: "Run"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        run = self.run.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "run": run,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.run import Run

        d = src_dict.copy()
        run = Run.from_dict(d.pop("run"))

        schema = d.pop("$schema", UNSET)

        describe_run_response = cls(
            run=run,
            schema=schema,
        )

        return describe_run_response
