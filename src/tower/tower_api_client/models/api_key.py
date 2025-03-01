import datetime
from typing import Any, Dict, Optional, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="APIKey")


@attr.s(auto_attribs=True)
class APIKey:
    """
    Attributes:
        created_at (datetime.datetime):
        identifier (str):
        name (str):
        last_used_at (Optional[datetime.datetime]):
    """

    created_at: datetime.datetime
    identifier: str
    name: str
    last_used_at: Optional[datetime.datetime]

    def to_dict(self) -> Dict[str, Any]:
        created_at = self.created_at.isoformat()

        identifier = self.identifier
        name = self.name
        last_used_at = self.last_used_at.isoformat() if self.last_used_at else None

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "identifier": identifier,
                "name": name,
                "last_used_at": last_used_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        created_at = isoparse(d.pop("created_at"))

        identifier = d.pop("identifier")

        name = d.pop("name")

        _last_used_at = d.pop("last_used_at")
        last_used_at: Optional[datetime.datetime]
        if _last_used_at is None:
            last_used_at = None
        else:
            last_used_at = isoparse(_last_used_at)

        api_key = cls(
            created_at=created_at,
            identifier=identifier,
            name=name,
            last_used_at=last_used_at,
        )

        return api_key
