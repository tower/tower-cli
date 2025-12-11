from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppParams")


@_attrs_define
class UpdateAppParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppParams.json.
        description (Union[None, Unset, str]): New description for the App
        is_externally_accessible (Union[None, Unset, bool]): Indicates that web traffic should be routed to this app and
            that its runs should get a hostname assigned to it.
        status (Union[None, Unset, str]): New status for the App
        subdomain (Union[None, Unset, str]): The subdomain this app is accessible under. Requires
            is_externally_accessible to be true.
    """

    schema: Union[Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    is_externally_accessible: Union[None, Unset, bool] = UNSET
    status: Union[None, Unset, str] = UNSET
    subdomain: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_externally_accessible: Union[None, Unset, bool]
        if isinstance(self.is_externally_accessible, Unset):
            is_externally_accessible = UNSET
        else:
            is_externally_accessible = self.is_externally_accessible

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        subdomain: Union[None, Unset, str]
        if isinstance(self.subdomain, Unset):
            subdomain = UNSET
        else:
            subdomain = self.subdomain

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if description is not UNSET:
            field_dict["description"] = description
        if is_externally_accessible is not UNSET:
            field_dict["is_externally_accessible"] = is_externally_accessible
        if status is not UNSET:
            field_dict["status"] = status
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_is_externally_accessible(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_externally_accessible = _parse_is_externally_accessible(
            d.pop("is_externally_accessible", UNSET)
        )

        def _parse_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_subdomain(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subdomain = _parse_subdomain(d.pop("subdomain", UNSET))

        update_app_params = cls(
            schema=schema,
            description=description,
            is_externally_accessible=is_externally_accessible,
            status=status,
            subdomain=subdomain,
        )

        return update_app_params
