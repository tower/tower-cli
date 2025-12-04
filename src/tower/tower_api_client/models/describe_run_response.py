from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.describe_run_links import DescribeRunLinks
    from ..models.run import Run


T = TypeVar("T", bound="DescribeRunResponse")


@_attrs_define
class DescribeRunResponse:
    """
    Attributes:
        links (DescribeRunLinks):
        run (Run):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/DescribeRunResponse.json.
    """

    links: "DescribeRunLinks"
    run: "Run"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        links = self.links.to_dict()

        run = self.run.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "$links": links,
                "run": run,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.describe_run_links import DescribeRunLinks
        from ..models.run import Run

        d = dict(src_dict)
        links = DescribeRunLinks.from_dict(d.pop("$links"))

        run = Run.from_dict(d.pop("run"))

        schema = d.pop("$schema", UNSET)

        describe_run_response = cls(
            links=links,
            run=run,
            schema=schema,
        )

        return describe_run_response
