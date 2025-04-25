import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.parameter import Parameter


T = TypeVar("T", bound="AppVersion")


@_attrs_define
class AppVersion:
    """
    Attributes:
        created_at (datetime.datetime):
        parameters (list['Parameter']):
        towerfile (str): The Towerfile that this version was created from.
        version (str):
    """

    created_at: datetime.datetime
    parameters: list["Parameter"]
    towerfile: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        parameters = []
        for parameters_item_data in self.parameters:
            parameters_item = parameters_item_data.to_dict()
            parameters.append(parameters_item)

        towerfile = self.towerfile

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "created_at": created_at,
                "parameters": parameters,
                "towerfile": towerfile,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.parameter import Parameter

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        parameters = []
        _parameters = d.pop("parameters")
        for parameters_item_data in _parameters:
            parameters_item = Parameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        towerfile = d.pop("towerfile")

        version = d.pop("version")

        app_version = cls(
            created_at=created_at,
            parameters=parameters,
            towerfile=towerfile,
            version=version,
        )

        return app_version
