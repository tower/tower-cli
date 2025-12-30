from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAccountParams")


@_attrs_define
class UpdateAccountParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAccountParams.json.
        is_self_hosted_only (Union[Unset, bool]): Whether the account is for self-hosted use only
        name (Union[Unset, str]): The new name for the account, if any
    """

    schema: Union[Unset, str] = UNSET
    is_self_hosted_only: Union[Unset, bool] = UNSET
    name: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        is_self_hosted_only = self.is_self_hosted_only

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if is_self_hosted_only is not UNSET:
            field_dict["is_self_hosted_only"] = is_self_hosted_only
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        is_self_hosted_only = d.pop("is_self_hosted_only", UNSET)

        name = d.pop("name", UNSET)

        update_account_params = cls(
            schema=schema,
            is_self_hosted_only=is_self_hosted_only,
            name=name,
        )

        return update_account_params
