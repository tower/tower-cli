from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAppParams")


@_attrs_define
class UpdateAppParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppParams.json.
        description (None | str | Unset): New description for the App
        is_externally_accessible (bool | None | Unset): Indicates that web traffic should be routed to this app and that
            its runs should get a hostname assigned to it.
        pending_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in pending
            state before being marked as failed.
        running_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in running
            state before being marked as failed.
        status (None | str | Unset): New status for the App
        subdomain (None | str | Unset): The subdomain this app is accessible under. Requires is_externally_accessible to
            be true.
    """

    schema: str | Unset = UNSET
    description: None | str | Unset = UNSET
    is_externally_accessible: bool | None | Unset = UNSET
    pending_timeout: int | None | Unset = UNSET
    running_timeout: int | None | Unset = UNSET
    status: None | str | Unset = UNSET
    subdomain: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        schema = self.schema

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_externally_accessible: bool | None | Unset
        if isinstance(self.is_externally_accessible, Unset):
            is_externally_accessible = UNSET
        else:
            is_externally_accessible = self.is_externally_accessible

        pending_timeout: int | None | Unset
        if isinstance(self.pending_timeout, Unset):
            pending_timeout = UNSET
        else:
            pending_timeout = self.pending_timeout

        running_timeout: int | None | Unset
        if isinstance(self.running_timeout, Unset):
            running_timeout = UNSET
        else:
            running_timeout = self.running_timeout

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        subdomain: None | str | Unset
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
        if pending_timeout is not UNSET:
            field_dict["pending_timeout"] = pending_timeout
        if running_timeout is not UNSET:
            field_dict["running_timeout"] = running_timeout
        if status is not UNSET:
            field_dict["status"] = status
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        schema = d.pop("$schema", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_is_externally_accessible(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_externally_accessible = _parse_is_externally_accessible(
            d.pop("is_externally_accessible", UNSET)
        )

        def _parse_pending_timeout(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        pending_timeout = _parse_pending_timeout(d.pop("pending_timeout", UNSET))

        def _parse_running_timeout(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        running_timeout = _parse_running_timeout(d.pop("running_timeout", UNSET))

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_subdomain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subdomain = _parse_subdomain(d.pop("subdomain", UNSET))

        update_app_params = cls(
            schema=schema,
            description=description,
            is_externally_accessible=is_externally_accessible,
            pending_timeout=pending_timeout,
            running_timeout=running_timeout,
            status=status,
            subdomain=subdomain,
        )

        return update_app_params
