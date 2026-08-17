from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_tag import AppTag
    from ..models.run_retry_policy import RunRetryPolicy


T = TypeVar("T", bound="UpdateAppParams")


@_attrs_define
class UpdateAppParams:
    """
    Attributes:
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAppParams.json.
        description (None | str | Unset): Deprecated: use short_description instead.
        is_externally_accessible (bool | None | Unset): Indicates that web traffic should be routed to this app and that
            its runs should get a hostname assigned to it.
        pending_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in pending
            state before being marked as failed.
        retry_policy (RunRetryPolicy | Unset):
        running_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in running
            state before being marked as failed.
        short_description (None | str | Unset): New description for the app.
        status (None | str | Unset): New status for the App
        subdomain (None | str | Unset): The subdomain this app is accessible under. Requires is_externally_accessible to
            be true.
        tags (list[AppTag] | Unset): The tags for this app.
    """

    schema: str | Unset = UNSET
    description: None | str | Unset = UNSET
    is_externally_accessible: bool | None | Unset = UNSET
    pending_timeout: int | None | Unset = UNSET
    retry_policy: RunRetryPolicy | Unset = UNSET
    running_timeout: int | None | Unset = UNSET
    short_description: None | str | Unset = UNSET
    status: None | str | Unset = UNSET
    subdomain: None | str | Unset = UNSET
    tags: list[AppTag] | Unset = UNSET

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

        retry_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.retry_policy, Unset):
            retry_policy = self.retry_policy.to_dict()

        running_timeout: int | None | Unset
        if isinstance(self.running_timeout, Unset):
            running_timeout = UNSET
        else:
            running_timeout = self.running_timeout

        short_description: None | str | Unset
        if isinstance(self.short_description, Unset):
            short_description = UNSET
        else:
            short_description = self.short_description

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

        tags: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = []
            for tags_item_data in self.tags:
                tags_item = tags_item_data.to_dict()
                tags.append(tags_item)

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
        if retry_policy is not UNSET:
            field_dict["retry_policy"] = retry_policy
        if running_timeout is not UNSET:
            field_dict["running_timeout"] = running_timeout
        if short_description is not UNSET:
            field_dict["short_description"] = short_description
        if status is not UNSET:
            field_dict["status"] = status
        if subdomain is not UNSET:
            field_dict["subdomain"] = subdomain
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_tag import AppTag
        from ..models.run_retry_policy import RunRetryPolicy

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

        _retry_policy = d.pop("retry_policy", UNSET)
        retry_policy: RunRetryPolicy | Unset
        if isinstance(_retry_policy, Unset):
            retry_policy = UNSET
        else:
            retry_policy = RunRetryPolicy.from_dict(_retry_policy)

        def _parse_running_timeout(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        running_timeout = _parse_running_timeout(d.pop("running_timeout", UNSET))

        def _parse_short_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        short_description = _parse_short_description(d.pop("short_description", UNSET))

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

        _tags = d.pop("tags", UNSET)
        tags: list[AppTag] | Unset = UNSET
        if _tags is not UNSET:
            tags = []
            for tags_item_data in _tags:
                tags_item = AppTag.from_dict(tags_item_data)

                tags.append(tags_item)

        update_app_params = cls(
            schema=schema,
            description=description,
            is_externally_accessible=is_externally_accessible,
            pending_timeout=pending_timeout,
            retry_policy=retry_policy,
            running_timeout=running_timeout,
            short_description=short_description,
            status=status,
            subdomain=subdomain,
            tags=tags,
        )

        return update_app_params
