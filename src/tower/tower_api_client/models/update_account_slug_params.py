from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateAccountSlugParams")


@attr.s(auto_attribs=True)
class UpdateAccountSlugParams:
    """
    Attributes:
        new_slug (str): The new slug for the account
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateAccountSlugParams.json.
    """

    new_slug: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        new_slug = self.new_slug
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "new_slug": new_slug,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        new_slug = d.pop("new_slug")

        schema = d.pop("$schema", UNSET)

        update_account_slug_params = cls(
            new_slug=new_slug,
            schema=schema,
        )

        return update_account_slug_params
