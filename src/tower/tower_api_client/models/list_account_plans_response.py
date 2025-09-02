from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.plan import Plan


T = TypeVar("T", bound="ListAccountPlansResponse")


@_attrs_define
class ListAccountPlansResponse:
    """
    Attributes:
        pages (Pagination):
        plans (list['Plan']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListAccountPlansResponse.json.
    """

    pages: "Pagination"
    plans: list["Plan"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        plans = []
        for plans_item_data in self.plans:
            plans_item = plans_item_data.to_dict()
            plans.append(plans_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "pages": pages,
                "plans": plans,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.plan import Plan

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        plans = []
        _plans = d.pop("plans")
        for plans_item_data in _plans:
            plans_item = Plan.from_dict(plans_item_data)

            plans.append(plans_item)

        schema = d.pop("$schema", UNSET)

        list_account_plans_response = cls(
            pages=pages,
            plans=plans,
            schema=schema,
        )

        return list_account_plans_response
