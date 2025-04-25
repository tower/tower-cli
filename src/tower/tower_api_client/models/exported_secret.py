import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="ExportedSecret")


@_attrs_define
class ExportedSecret:
    """
    Attributes:
        created_at (datetime.datetime):
        encrypted_value (str):
        environment (str):
        name (str):
    """

    created_at: datetime.datetime
    encrypted_value: str
    environment: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        encrypted_value = self.encrypted_value

        environment = self.environment

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "encrypted_value": encrypted_value,
                "environment": environment,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        encrypted_value = d.pop("encrypted_value")

        environment = d.pop("environment")

        name = d.pop("name")

        exported_secret = cls(
            created_at=created_at,
            encrypted_value=encrypted_value,
            environment=environment,
            name=name,
        )

        return exported_secret
