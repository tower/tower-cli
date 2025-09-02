from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateTeamParams")


@_attrs_define
class UpdateTeamParams:
    """
    Attributes:
        name (Union[None, str]): The name of the team to update. This is optional, if you supply null it will not update
            the team name.
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/UpdateTeamParams.json.
    """

    name: Union[None, str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: Union[None, str]
        name = self.name

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        name = _parse_name(d.pop("name"))

        schema = d.pop("$schema", UNSET)

        update_team_params = cls(
            name=name,
            schema=schema,
        )

        return update_team_params
