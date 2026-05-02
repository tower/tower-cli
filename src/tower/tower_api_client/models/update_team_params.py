from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.update_team_params_execution_region import UpdateTeamParamsExecutionRegion
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateTeamParams")


@_attrs_define
class UpdateTeamParams:
    """
    Attributes:
        name (None | str): The name of the team to update. This is optional, if you supply null it will not update the
            team name.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateTeamParams.json.
        execution_region (UpdateTeamParamsExecutionRegion | Unset): The execution region for runs (eu-central-1 or us-
            east-1)
    """

    name: None | str
    schema: str | Unset = UNSET
    execution_region: UpdateTeamParamsExecutionRegion | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str
        name = self.name

        schema = self.schema

        execution_region: str | Unset = UNSET
        if not isinstance(self.execution_region, Unset):
            execution_region = self.execution_region.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if execution_region is not UNSET:
            field_dict["execution_region"] = execution_region

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        schema = d.pop("$schema", UNSET)

        _execution_region = d.pop("execution_region", UNSET)
        execution_region: UpdateTeamParamsExecutionRegion | Unset
        if isinstance(_execution_region, Unset):
            execution_region = UNSET
        else:
            execution_region = UpdateTeamParamsExecutionRegion(_execution_region)

        update_team_params = cls(
            name=name,
            schema=schema,
            execution_region=execution_region,
        )

        return update_team_params
