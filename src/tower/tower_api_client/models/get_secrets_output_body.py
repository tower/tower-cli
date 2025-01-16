from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination import Pagination
    from ..models.secret import Secret


T = TypeVar("T", bound="GetSecretsOutputBody")


@_attrs_define
class GetSecretsOutputBody:
    """
    Attributes:
        pages (Pagination):
        secrets (Union[None, list['Secret']]):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    pages: "Pagination"
    secrets: Union[None, list["Secret"]]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pages = self.pages.to_dict()

        secrets: Union[None, list[dict[str, Any]]]
        if isinstance(self.secrets, list):
            secrets = []
            for secrets_type_0_item_data in self.secrets:
                secrets_type_0_item = secrets_type_0_item_data.to_dict()
                secrets.append(secrets_type_0_item)

        else:
            secrets = self.secrets

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
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.pagination import Pagination
        from ..models.secret import Secret

        d = src_dict.copy()
        pages = Pagination.from_dict(d.pop("pages"))

        def _parse_secrets(data: object) -> Union[None, list["Secret"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                secrets_type_0 = []
                _secrets_type_0 = data
                for secrets_type_0_item_data in _secrets_type_0:
                    secrets_type_0_item = Secret.from_dict(secrets_type_0_item_data)

                    secrets_type_0.append(secrets_type_0_item)

                return secrets_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["Secret"]], data)

        secrets = _parse_secrets(d.pop("secrets"))

        schema = d.pop("$schema", UNSET)

        get_secrets_output_body = cls(
            pages=pages,
            secrets=secrets,
            schema=schema,
        )

        return get_secrets_output_body
