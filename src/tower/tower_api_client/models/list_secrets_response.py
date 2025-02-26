from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.secret import Secret


T = TypeVar("T", bound="ListSecretsResponse")


@attr.s(auto_attribs=True)
class ListSecretsResponse:
    """
    Attributes:
        pages (Pagination):
        secrets (List['Secret']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListSecretsResponse.json.
    """

    pages: "Pagination"
    secrets: List["Secret"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        pages = self.pages.to_dict()

        secrets = []
        for secrets_item_data in self.secrets:
            secrets_item = secrets_item_data.to_dict()

            secrets.append(secrets_item)

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "pages": pages,
                "secrets": secrets,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.secret import Secret

        d = src_dict.copy()
        pages = Pagination.from_dict(d.pop("pages"))

        secrets = []
        _secrets = d.pop("secrets")
        for secrets_item_data in _secrets:
            secrets_item = Secret.from_dict(secrets_item_data)

            secrets.append(secrets_item)

        schema = d.pop("$schema", UNSET)

        list_secrets_response = cls(
            pages=pages,
            secrets=secrets,
            schema=schema,
        )

        return list_secrets_response
