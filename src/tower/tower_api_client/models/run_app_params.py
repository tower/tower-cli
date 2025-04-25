from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_app_params_parameters import RunAppParamsParameters


T = TypeVar("T", bound="RunAppParams")


@_attrs_define
class RunAppParams:
    """
    Attributes:
        environment (str): The environment to run this app in.
        parameters (RunAppParamsParameters): The parameters to pass into this app.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RunAppParams.json.
        parent_run_id (Union[None, Unset, str]): The ID of the run that invoked this run, if relevant. Should be null,
            if none.
    """

    environment: str
    parameters: "RunAppParamsParameters"
    schema: Union[Unset, str] = UNSET
    parent_run_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        parameters = self.parameters.to_dict()

        schema = self.schema

        parent_run_id: Union[None, Unset, str]
        if isinstance(self.parent_run_id, Unset):
            parent_run_id = UNSET
        else:
            parent_run_id = self.parent_run_id

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environment": environment,
                "parameters": parameters,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if parent_run_id is not UNSET:
            field_dict["parent_run_id"] = parent_run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_app_params_parameters import RunAppParamsParameters

        d = dict(src_dict)
        environment = d.pop("environment")

        parameters = RunAppParamsParameters.from_dict(d.pop("parameters"))

        schema = d.pop("$schema", UNSET)

        def _parse_parent_run_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        parent_run_id = _parse_parent_run_id(d.pop("parent_run_id", UNSET))

        run_app_params = cls(
            environment=environment,
            parameters=parameters,
            schema=schema,
            parent_run_id=parent_run_id,
        )

        return run_app_params
