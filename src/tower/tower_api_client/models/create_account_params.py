from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAccountParams")


@attr.s(auto_attribs=True)
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
            http://localhost:8081/v1/schemas/CreateAccountParams.json.
    """

    company: str
    country: str
    email: str
    first_name: str
    invite: str
    last_name: str
    password: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        company = self.company
        country = self.country
        email = self.email
        first_name = self.first_name
        invite = self.invite
        last_name = self.last_name
        password = self.password
        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
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
