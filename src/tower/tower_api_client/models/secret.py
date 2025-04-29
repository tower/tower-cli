import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="Secret")


@_attrs_define
class Secret:
    """
    Attributes:
        created_at (datetime.datetime):
        environment (str):
        name (str):
        preview (str):
    """

    created_at: datetime.datetime
    environment: str
    name: str
    preview: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        environment = self.environment

        name = self.name

        preview = self.preview

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "environment": environment,
                "name": name,
                "preview": preview,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        environment = d.pop("environment")

        name = d.pop("name")

        preview = d.pop("preview")

        secret = cls(
            created_at=created_at,
            environment=environment,
            name=name,
            preview=preview,
        )

        return secret
