from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExportCatalogsParams")


@_attrs_define
class ExportCatalogsParams:
    """
    Attributes:
        all_ (bool): Whether to fetch all catalogs or only the ones in the supplied environment. Default: False.
        environment (str): The environment to filter by. Default: 'default'.
        page (int): The page number to fetch. Default: 1.
        page_size (int): The number of records to fetch on each page. Default: 20.
        public_key (str): The PEM-encoded public key you want to use to encrypt sensitive catalog properties.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/ExportCatalogsParams.json.
    """

    public_key: str
    all_: bool = False
    environment: str = "default"
    page: int = 1
    page_size: int = 20
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        all_ = self.all_

        environment = self.environment

        page = self.page

        page_size = self.page_size

        public_key = self.public_key

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "all": all_,
                "environment": environment,
                "page": page,
                "page_size": page_size,
                "public_key": public_key,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        all_ = d.pop("all")

        environment = d.pop("environment")

        page = d.pop("page")

        page_size = d.pop("page_size")

        public_key = d.pop("public_key")

        schema = d.pop("$schema", UNSET)

        export_catalogs_params = cls(
            all_=all_,
            environment=environment,
            page=page,
            page_size=page_size,
            public_key=public_key,
            schema=schema,
        )

        return export_catalogs_params
