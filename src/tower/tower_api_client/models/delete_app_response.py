from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app import App


T = TypeVar("T", bound="DeleteAppResponse")


@attr.s(auto_attribs=True)
class DeleteAppResponse:
    """
    Attributes:
        app (App):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DeleteAppResponse.json.
    """

    app: "App"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        app = self.app.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "app": app,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.app import App

        d = src_dict.copy()
        app = App.from_dict(d.pop("app"))

        schema = d.pop("$schema", UNSET)

        delete_app_response = cls(
            app=app,
            schema=schema,
        )

        return delete_app_response
