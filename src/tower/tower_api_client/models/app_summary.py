from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run
    from ..models.run_results import RunResults


T = TypeVar("T", bound="AppSummary")


@_attrs_define
class AppSummary:
    """
    Attributes:
        app (App):
        run_results (RunResults):
        runs (list['Run']):
        total_runs (int):
    """

    app: "App"
    run_results: "RunResults"
    runs: list["Run"]
    total_runs: int

    def to_dict(self) -> dict[str, Any]:
        app = self.app.to_dict()

        run_results = self.run_results.to_dict()

        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()
            runs.append(runs_item)

        total_runs = self.total_runs

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
                "run_results": run_results,
                "runs": runs,
                "total_runs": total_runs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run
        from ..models.run_results import RunResults

        d = dict(src_dict)
        app = App.from_dict(d.pop("app"))

        run_results = RunResults.from_dict(d.pop("run_results"))

        runs = []
        _runs = d.pop("runs")
        for runs_item_data in _runs:
            runs_item = Run.from_dict(runs_item_data)

            runs.append(runs_item)

        total_runs = d.pop("total_runs")

        app_summary = cls(
            app=app,
            run_results=run_results,
            runs=runs,
            total_runs=total_runs,
        )

        return app_summary
