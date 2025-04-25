from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAccountParams")


@_attrs_define
class CreateAccountParams:
    """
    Attributes:
        company (str):
        country (str):
        email (str):
        first_name (str):
        invite (str):
        last_name (str):
        password (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateAccountParams.json.
    """

    company: str
    country: str
    email: str
    first_name: str
    invite: str
    last_name: str
    password: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        company = self.company

        country = self.country

        email = self.email

        first_name = self.first_name

        invite = self.invite

        last_name = self.last_name

        password = self.password

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "company": company,
                "country": country,
                "email": email,
                "first_name": first_name,
                "invite": invite,
                "last_name": last_name,
                "password": password,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        company = d.pop("company")

        country = d.pop("country")

        email = d.pop("email")

        first_name = d.pop("first_name")

        invite = d.pop("invite")

        last_name = d.pop("last_name")

        password = d.pop("password")

        schema = d.pop("$schema", UNSET)

        create_account_params = cls(
            company=company,
            country=country,
            email=email,
            first_name=first_name,
            invite=invite,
            last_name=last_name,
            password=password,
            schema=schema,
        )

        return create_account_params
