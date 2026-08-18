from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_tag import AppTag
    from ..models.run_retry_policy import RunRetryPolicy


T = TypeVar("T", bound="CreateAppParams")


@_attrs_define
class CreateAppParams:
    """
    Attributes:
        name (str): The name of the app.
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAppParams.json.
        is_externally_accessible (bool | Unset): Indicates that web traffic should be routed to this app and that its
            runs should get a hostname assigned to it. Default: False.
        pending_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in pending
            state before being marked as failed.
        retry_policy (RunRetryPolicy | Unset):
        running_timeout (int | None | Unset): The amount of time in seconds that runs of this app can stay in running
            state before being marked as failed.
        short_description (str | Unset): A description of the app.
        slug (str | Unset): The slug of the app. Legacy CLI will send it but we don't need it.
        subdomain (None | str | Unset): The subdomain this app is accessible under. Requires is_externally_accessible to
            be true.
        tags (list[AppTag] | Unset): The tags for this app.
    """

    name: str
    schema: str | Unset = UNSET
    is_externally_accessible: bool | Unset = False
    pending_timeout: int | None | Unset = UNSET
    retry_policy: RunRetryPolicy | Unset = UNSET
    running_timeout: int | None | Unset = UNSET
    short_description: str | Unset = UNSET
    slug: str | Unset = UNSET
    subdomain: None | str | Unset = UNSET
    tags: list[AppTag] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        schema = self.schema

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

        short_description = self.short_description

        slug = self.slug

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

        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema
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
        if slug is not UNSET:
            field_dict["slug"] = slug
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
        name = d.pop("name")

        schema = d.pop("$schema", UNSET)

        is_externally_accessible = d.pop("is_externally_accessible", UNSET)

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

        short_description = d.pop("short_description", UNSET)

        slug = d.pop("slug", UNSET)

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

        create_app_params = cls(
            name=name,
            schema=schema,
            is_externally_accessible=is_externally_accessible,
            pending_timeout=pending_timeout,
            retry_policy=retry_policy,
            running_timeout=running_timeout,
            short_description=short_description,
            slug=slug,
            subdomain=subdomain,
            tags=tags,
        )

        return create_app_params
