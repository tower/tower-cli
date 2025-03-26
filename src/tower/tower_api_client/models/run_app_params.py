from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_app_params_parameters import RunAppParamsParameters


T = TypeVar("T", bound="RunAppParams")


@attr.s(auto_attribs=True)
class RunAppParams:
    """
    Attributes:
        environment (str): The environment to run this app in.
        parameters (RunAppParamsParameters): The parameters to pass into this app.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/RunAppParams.json.
        parent_run_id (Union[Unset, None, str]): The ID of the run that invoked this run, if relevant. Should be null,
            if none.
    """

    environment: str
    parameters: "RunAppParamsParameters"
    schema: Union[Unset, str] = UNSET
    parent_run_id: Union[Unset, None, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        environment = self.environment
        parameters = self.parameters.to_dict()

        schema = self.schema
        parent_run_id = self.parent_run_id

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.run_app_params_parameters import RunAppParamsParameters

        d = src_dict.copy()
        environment = d.pop("environment")

        parameters = RunAppParamsParameters.from_dict(d.pop("parameters"))

        schema = d.pop("$schema", UNSET)

        parent_run_id = d.pop("parent_run_id", UNSET)

        run_app_params = cls(
            environment=environment,
            parameters=parameters,
            schema=schema,
            parent_run_id=parent_run_id,
        )

        return run_app_params
