from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app import App


T = TypeVar("T", bound="UpdateAppResponse")


@_attrs_define
class UpdateAppResponse:
    """
    Attributes:
        App (App):
        app (App):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppResponse.json.
    """

    App: App
    app: App
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.app import App

        App = self.App.to_dict()

        app = self.app.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "App": App,
                "app": app,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app import App

        d = dict(src_dict)
        App = App.from_dict(d.pop("App"))

        app = App.from_dict(d.pop("app"))

        schema = d.pop("$schema", UNSET)

        update_app_response = cls(
            App=App,
            app=app,
            schema=schema,
        )

        return update_app_response
