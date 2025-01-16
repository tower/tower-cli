from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flags_struct import FlagsStruct


T = TypeVar("T", bound="PostAccountInputBody")


@_attrs_define
class PostAccountInputBody:
    """
    Attributes:
        company (str):
        country (str):
        email (str):
        first_name (str):
        flags (FlagsStruct):
        invite (str):
        last_name (str):
        password (str):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    company: str
    country: str
    email: str
    first_name: str
    flags: "FlagsStruct"
    invite: str
    last_name: str
    password: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        company = self.company

        country = self.country

        email = self.email

        first_name = self.first_name

        flags = self.flags.to_dict()

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
                "flags": flags,
                "invite": invite,
                "last_name": last_name,
                "password": password,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.flags_struct import FlagsStruct

        d = src_dict.copy()
        company = d.pop("company")

        country = d.pop("country")

        email = d.pop("email")

        first_name = d.pop("first_name")

        flags = FlagsStruct.from_dict(d.pop("flags"))

        invite = d.pop("invite")

        last_name = d.pop("last_name")

        password = d.pop("password")

        schema = d.pop("$schema", UNSET)

        post_account_input_body = cls(
            company=company,
            country=country,
            email=email,
            first_name=first_name,
            flags=flags,
            invite=invite,
            last_name=last_name,
            password=password,
            schema=schema,
        )

        return post_account_input_body
