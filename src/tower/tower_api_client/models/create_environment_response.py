from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.environment import Environment


T = TypeVar("T", bound="CreateEnvironmentResponse")


@_attrs_define
class CreateEnvironmentResponse:
    """
    Attributes:
        environment (Environment):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateEnvironmentResponse.json.
    """

    environment: "Environment"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.environment import Environment

        d = dict(src_dict)
        environment = Environment.from_dict(d.pop("environment"))

        schema = d.pop("$schema", UNSET)

        create_environment_response = cls(
            environment=environment,
            schema=schema,
        )

        return create_environment_response
