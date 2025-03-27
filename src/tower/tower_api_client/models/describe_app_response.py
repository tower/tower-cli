from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run


T = TypeVar("T", bound="DescribeAppResponse")


@attr.s(auto_attribs=True)
class DescribeAppResponse:
    """
    Attributes:
        app (App):
        runs (List['Run']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DescribeAppResponse.json.
    """

    app: "App"
    runs: List["Run"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        app = self.app.to_dict()

        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()

            runs.append(runs_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
                "runs": runs,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run

        d = src_dict.copy()
        app = App.from_dict(d.pop("app"))

        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = Run.from_dict(runs_item_data)

            runs.append(runs_item)

        schema = d.pop("$schema", UNSET)

        describe_app_response = cls(
            app=app,
            runs=runs,
            schema=schema,
        )

        return describe_app_response
