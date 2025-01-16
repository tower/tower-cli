from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_app_runs_input_body_parameters import PostAppRunsInputBodyParameters


T = TypeVar("T", bound="PostAppRunsInputBody")


@_attrs_define
class PostAppRunsInputBody:
    """
    Attributes:
        environment (str):
        parameters (PostAppRunsInputBodyParameters):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    environment: str
    parameters: "PostAppRunsInputBodyParameters"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        parameters = self.parameters.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
                "parameters": parameters,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.post_app_runs_input_body_parameters import PostAppRunsInputBodyParameters

        d = src_dict.copy()
        environment = d.pop("environment")

        parameters = PostAppRunsInputBodyParameters.from_dict(d.pop("parameters"))

        schema = d.pop("$schema", UNSET)

        post_app_runs_input_body = cls(
            environment=environment,
            parameters=parameters,
            schema=schema,
        )

        return post_app_runs_input_body
