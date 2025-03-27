import datetime
from typing import Any, Dict, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="Secret")


@attr.s(auto_attribs=True)
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

    def to_dict(self) -> Dict[str, Any]:
        created_at = self.created_at.isoformat()

        environment = self.environment
        name = self.name
        preview = self.preview

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
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
