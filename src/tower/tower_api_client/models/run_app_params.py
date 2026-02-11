from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_app_initiator_data import RunAppInitiatorData
    from ..models.run_app_params_parameters import RunAppParamsParameters


T = TypeVar("T", bound="RunAppParams")


@_attrs_define
class RunAppParams:
    """
    Attributes:
        environment (str): The environment to run this app in.
        parameters (RunAppParamsParameters): The parameters to pass into this app.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RunAppParams.json.
        initiator (RunAppInitiatorData | Unset):
        parent_run_id (None | str | Unset): The ID of the run that invoked this run, if relevant. Should be null, if
            none.
    """

    environment: str
    parameters: RunAppParamsParameters
    schema: str | Unset = UNSET
    initiator: RunAppInitiatorData | Unset = UNSET
    parent_run_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        environment = self.environment

        parameters = self.parameters.to_dict()

        schema = self.schema

        initiator: dict[str, Any] | Unset = UNSET
        if not isinstance(self.initiator, Unset):
            initiator = self.initiator.to_dict()

        parent_run_id: None | str | Unset
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
        if initiator is not UNSET:
            field_dict["initiator"] = initiator
        if parent_run_id is not UNSET:
            field_dict["parent_run_id"] = parent_run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_app_initiator_data import RunAppInitiatorData
        from ..models.run_app_params_parameters import RunAppParamsParameters

        d = dict(src_dict)
        environment = d.pop("environment")

        parameters = RunAppParamsParameters.from_dict(d.pop("parameters"))

        schema = d.pop("$schema", UNSET)

        _initiator = d.pop("initiator", UNSET)
        initiator: RunAppInitiatorData | Unset
        if isinstance(_initiator, Unset):
            initiator = UNSET
        else:
            initiator = RunAppInitiatorData.from_dict(_initiator)

        def _parse_parent_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_run_id = _parse_parent_run_id(d.pop("parent_run_id", UNSET))

        run_app_params = cls(
            environment=environment,
            parameters=parameters,
            schema=schema,
            initiator=initiator,
            parent_run_id=parent_run_id,
        )

        return run_app_params
