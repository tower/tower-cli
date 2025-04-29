import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

T = TypeVar("T", bound="APIKey")


@_attrs_define
class APIKey:
    """
    Attributes:
        created_at (datetime.datetime):
        identifier (str):
        last_used_at (Union[None, datetime.datetime]):
        name (str):
    """

    created_at: datetime.datetime
    identifier: str
    last_used_at: Union[None, datetime.datetime]
    name: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        identifier = self.identifier

        last_used_at: Union[None, str]
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "identifier": identifier,
                "last_used_at": last_used_at,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        identifier = d.pop("identifier")

        def _parse_last_used_at(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = isoparse(data)

                return last_used_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

        name = d.pop("name")

        api_key = cls(
            created_at=created_at,
            identifier=identifier,
            last_used_at=last_used_at,
            name=name,
        )

        return api_key
