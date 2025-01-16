from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app import App


T = TypeVar("T", bound="PostAppsOutputBody")


@_attrs_define
class PostAppsOutputBody:
    """
    Attributes:
        app (App):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    app: "App"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        app = self.app.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.app import App

        d = src_dict.copy()
        app = App.from_dict(d.pop("app"))

        schema = d.pop("$schema", UNSET)

        post_apps_output_body = cls(
            app=app,
            schema=schema,
        )

        return post_apps_output_body
