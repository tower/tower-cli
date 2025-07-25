from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.runner_credentials import RunnerCredentials


T = TypeVar("T", bound="GenerateRunnerCredentialsResponse")


@_attrs_define
class GenerateRunnerCredentialsResponse:
    """
    Attributes:
        credentials (RunnerCredentials):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/GenerateRunnerCredentialsResponse.json.
    """

    credentials: "RunnerCredentials"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        credentials = self.credentials.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "credentials": credentials,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.runner_credentials import RunnerCredentials

        d = dict(src_dict)
        credentials = RunnerCredentials.from_dict(d.pop("credentials"))

        schema = d.pop("$schema", UNSET)

        generate_runner_credentials_response = cls(
            credentials=credentials,
            schema=schema,
        )

        return generate_runner_credentials_response
