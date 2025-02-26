from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateUserParams")


@attr.s(auto_attribs=True)
class UpdateUserParams:
    """
    Attributes:
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/UpdateUserParams.json.
        company (Union[Unset, None, str]):
        country (Union[Unset, None, str]):
        first_name (Union[Unset, None, str]):
        last_name (Union[Unset, None, str]):
    """

    schema: Union[Unset, str] = UNSET
    company: Union[Unset, None, str] = UNSET
    country: Union[Unset, None, str] = UNSET
    first_name: Union[Unset, None, str] = UNSET
    last_name: Union[Unset, None, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        schema = self.schema
        company = self.company
        country = self.country
        first_name = self.first_name
        last_name = self.last_name

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if schema is not UNSET:
            field_dict["$schema"] = schema
        if company is not UNSET:
            field_dict["company"] = company
        if country is not UNSET:
            field_dict["country"] = country
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        schema = d.pop("$schema", UNSET)

        company = d.pop("company", UNSET)

        country = d.pop("country", UNSET)

        first_name = d.pop("first_name", UNSET)

        last_name = d.pop("last_name", UNSET)

        update_user_params = cls(
            schema=schema,
            company=company,
            country=country,
            first_name=first_name,
            last_name=last_name,
        )

        return update_user_params
