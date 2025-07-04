from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.verified_authenticator import VerifiedAuthenticator


T = TypeVar("T", bound="ListAuthenticatorsResponse")


@_attrs_define
class ListAuthenticatorsResponse:
    """
    Attributes:
        authenticators (list['VerifiedAuthenticator']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ListAuthenticatorsResponse.json.
    """

    authenticators: list["VerifiedAuthenticator"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        authenticators = []
        for authenticators_item_data in self.authenticators:
            authenticators_item = authenticators_item_data.to_dict()
            authenticators.append(authenticators_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "authenticators": authenticators,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.verified_authenticator import VerifiedAuthenticator

        d = dict(src_dict)
        authenticators = []
        _authenticators = d.pop("authenticators")
        for authenticators_item_data in _authenticators:
            authenticators_item = VerifiedAuthenticator.from_dict(
                authenticators_item_data
            )

            authenticators.append(authenticators_item)

        schema = d.pop("$schema", UNSET)

        list_authenticators_response = cls(
            authenticators=authenticators,
            schema=schema,
        )

        return list_authenticators_response
