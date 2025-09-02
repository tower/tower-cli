from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppParams")


@_attrs_define
class UpdateAppParams:
    """
    Attributes:
        description (str): New description for the App
        status (str): New status for the App
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppParams.json.
        is_externally_accessible (Union[None, Unset, bool]): Indicates that web traffic should be routed to this app and
            that its runs should get a hostname assigned to it.
    """

    description: str
    status: str
    schema: Union[Unset, str] = UNSET
    is_externally_accessible: Union[None, Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        status = self.status

        schema = self.schema

        is_externally_accessible: Union[None, Unset, bool]
        if isinstance(self.is_externally_accessible, Unset):
            is_externally_accessible = UNSET
        else:
            is_externally_accessible = self.is_externally_accessible

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "description": description,
                "status": status,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if is_externally_accessible is not UNSET:
            field_dict["is_externally_accessible"] = is_externally_accessible

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description")

        status = d.pop("status")

        schema = d.pop("$schema", UNSET)

        def _parse_is_externally_accessible(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_externally_accessible = _parse_is_externally_accessible(
            d.pop("is_externally_accessible", UNSET)
        )

        update_app_params = cls(
            description=description,
            status=status,
            schema=schema,
            is_externally_accessible=is_externally_accessible,
        )

        return update_app_params
