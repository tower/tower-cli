from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.organization import Organization


T = TypeVar("T", bound="UpdateOrganizationResponse")


@_attrs_define
class UpdateOrganizationResponse:
    """
    Attributes:
        organization (Organization):
        schema (str | Unset): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateOrganizationResponse.json.
    """

    organization: Organization
    schema: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        organization = self.organization.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "organization": organization,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization import Organization

        d = dict(src_dict)
        organization = Organization.from_dict(d.pop("organization"))

        schema = d.pop("$schema", UNSET)

        update_organization_response = cls(
            organization=organization,
            schema=schema,
        )

        return update_organization_response
