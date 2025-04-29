from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAccountSlugParams")


@_attrs_define
class UpdateAccountSlugParams:
    """
    Attributes:
        new_slug (str): The new slug for the account
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateAccountSlugParams.json.
    """

    new_slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        new_slug = self.new_slug

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "new_slug": new_slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_slug = d.pop("new_slug")

        schema = d.pop("$schema", UNSET)

        update_account_slug_params = cls(
            new_slug=new_slug,
            schema=schema,
        )

        return update_account_slug_params
