from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run


T = TypeVar("T", bound="AppSummary")


@_attrs_define
class AppSummary:
    """
    Attributes:
        app (App):
        runs (list['Run']):
    """

    app: "App"
    runs: list["Run"]

    def to_dict(self) -> dict[str, Any]:
        app = self.app.to_dict()

        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()
            runs.append(runs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
                "runs": runs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run

        d = dict(src_dict)
        app = App.from_dict(d.pop("app"))

        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = Run.from_dict(runs_item_data)

            runs.append(runs_item)

        app_summary = cls(
            app=app,
            runs=runs,
        )

        return app_summary
