from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run
    from ..models.run_results import RunResults


T = TypeVar("T", bound="AppSummary")


@attr.s(auto_attribs=True)
class AppSummary:
    """
    Attributes:
        app (App):
        run_results (RunResults):
        runs (List['Run']):
        total_runs (int):
    """

    app: "App"
    run_results: "RunResults"
    runs: List["Run"]
    total_runs: int

    def to_dict(self) -> Dict[str, Any]:
        app = self.app.to_dict()

        run_results = self.run_results.to_dict()

        runs = []
        for runs_item_data in self.runs:
            runs_item = runs_item_data.to_dict()

            runs.append(runs_item)

        total_runs = self.total_runs

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run
        from ..models.run_results import RunResults

        d = src_dict.copy()
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
