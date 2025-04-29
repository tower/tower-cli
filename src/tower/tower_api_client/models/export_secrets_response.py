from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.exported_secret import ExportedSecret
    from ..models.pagination import Pagination


T = TypeVar("T", bound="ExportSecretsResponse")


@_attrs_define
class ExportSecretsResponse:
    """
    Attributes:
        pages (Pagination):
        secrets (list['ExportedSecret']):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ExportSecretsResponse.json.
    """

    pages: "Pagination"
    secrets: list["ExportedSecret"]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        secrets = []
        for secrets_item_data in self.secrets:
            secrets_item = secrets_item_data.to_dict()
            secrets.append(secrets_item)

        schema = self.schema

        field_dict: dict[str, Any] = {}
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
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.exported_secret import ExportedSecret
        from ..models.pagination import Pagination

        d = dict(src_dict)
        pages = Pagination.from_dict(d.pop("pages"))

        secrets = []
        _secrets = d.pop("secrets")
        for secrets_item_data in _secrets:
            secrets_item = ExportedSecret.from_dict(secrets_item_data)

            secrets.append(secrets_item)

        schema = d.pop("$schema", UNSET)

        export_secrets_response = cls(
            pages=pages,
            secrets=secrets,
            schema=schema,
        )

        return export_secrets_response
