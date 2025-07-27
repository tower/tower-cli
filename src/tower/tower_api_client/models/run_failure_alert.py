from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run


T = TypeVar("T", bound="RunFailureAlert")


@_attrs_define
class RunFailureAlert:
    """
    Attributes:
        app (App):
        run (Run):
    """

    app: "App"
    run: "Run"

    def to_dict(self) -> dict[str, Any]:
        app = self.app.to_dict()

        run = self.run.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
                "run": run,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run

        d = dict(src_dict)
        app = App.from_dict(d.pop("app"))

        run = Run.from_dict(d.pop("run"))

        run_failure_alert = cls(
            app=app,
            run=run,
        )

        return run_failure_alert
