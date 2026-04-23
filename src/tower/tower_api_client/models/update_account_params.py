from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_account_params_execution_region import (
    UpdateAccountParamsExecutionRegion,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAccountParams")


@_attrs_define
class UpdateAccountParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example: https://api.staging.tower-
            dev.net/v1/schemas/UpdateAccountParams.json.
        execution_region (UpdateAccountParamsExecutionRegion | Unset): The execution region for runs (eu-central-1 or
            us-east-1)
        is_self_hosted_only (bool | Unset): Whether the account is for self-hosted use only
        name (str | Unset): The new name for the account, if any
    """

    schema: str | Unset = UNSET
    execution_region: UpdateAccountParamsExecutionRegion | Unset = UNSET
    is_self_hosted_only: bool | Unset = UNSET
    name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        execution_region: str | Unset = UNSET
        if not isinstance(self.execution_region, Unset):
            execution_region = self.execution_region.value

        is_self_hosted_only = self.is_self_hosted_only

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if execution_region is not UNSET:
            field_dict["execution_region"] = execution_region
        if is_self_hosted_only is not UNSET:
            field_dict["is_self_hosted_only"] = is_self_hosted_only
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        _execution_region = d.pop("execution_region", UNSET)
        execution_region: UpdateAccountParamsExecutionRegion | Unset
        if isinstance(_execution_region, Unset):
            execution_region = UNSET
        else:
            execution_region = UpdateAccountParamsExecutionRegion(_execution_region)

        is_self_hosted_only = d.pop("is_self_hosted_only", UNSET)

        name = d.pop("name", UNSET)

        update_account_params = cls(
            schema=schema,
            execution_region=execution_region,
            is_self_hosted_only=is_self_hosted_only,
            name=name,
        )

        return update_account_params
