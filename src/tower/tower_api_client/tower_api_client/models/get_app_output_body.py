from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app import App
    from ..models.run import Run


T = TypeVar("T", bound="GetAppOutputBody")


@_attrs_define
class GetAppOutputBody:
    """
    Attributes:
        app (App):
        runs (Union[None, list['Run']]):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    app: "App"
    runs: Union[None, list["Run"]]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        app = self.app.to_dict()

        runs: Union[None, list[dict[str, Any]]]
        if isinstance(self.runs, list):
            runs = []
            for runs_type_0_item_data in self.runs:
                runs_type_0_item = runs_type_0_item_data.to_dict()
                runs.append(runs_type_0_item)

        else:
            runs = self.runs

        schema = self.schema

        field_dict: dict[str, Any] = {}
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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.app import App
        from ..models.run import Run

        d = src_dict.copy()
        app = App.from_dict(d.pop("app"))

        def _parse_runs(data: object) -> Union[None, list["Run"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                runs_type_0 = []
                _runs_type_0 = data
                for runs_type_0_item_data in _runs_type_0:
                    runs_type_0_item = Run.from_dict(runs_type_0_item_data)

                    runs_type_0.append(runs_type_0_item)

                return runs_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["Run"]], data)

        runs = _parse_runs(d.pop("runs"))

        schema = d.pop("$schema", UNSET)

        get_app_output_body = cls(
            app=app,
            runs=runs,
            schema=schema,
        )

        return get_app_output_body
