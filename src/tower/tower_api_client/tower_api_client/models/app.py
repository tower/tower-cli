import datetime
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="App")


@_attrs_define
class App:
    """
    Attributes:
        created_at (datetime.datetime):
        last_run_at (datetime.datetime):
        name (str):
        owner (str):
        short_description (str):
        version (str):
    """

    created_at: datetime.datetime
    last_run_at: datetime.datetime
    name: str
    owner: str
    short_description: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        last_run_at = self.last_run_at.isoformat()

        name = self.name

        owner = self.owner

        short_description = self.short_description

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "last_run_at": last_run_at,
                "name": name,
                "owner": owner,
                "short_description": short_description,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        created_at = isoparse(d.pop("created_at"))

        last_run_at = isoparse(d.pop("last_run_at"))

        name = d.pop("name")

        owner = d.pop("owner")

        short_description = d.pop("short_description")

        version = d.pop("version")

        app = cls(
            created_at=created_at,
            last_run_at=last_run_at,
            name=name,
            owner=owner,
            short_description=short_description,
            version=version,
        )

        return app
