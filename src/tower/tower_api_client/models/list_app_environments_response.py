from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ListAppEnvironmentsResponse")


@attr.s(auto_attribs=True)
class ListAppEnvironmentsResponse:
    """
    Attributes:
        environments (List[str]):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/ListAppEnvironmentsResponse.json.
    """

    environments: List[str]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        environments = self.environments

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "environments": environments,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        environments = cast(List[str], d.pop("environments"))

        schema = d.pop("$schema", UNSET)

        list_app_environments_response = cls(
            environments=environments,
            schema=schema,
        )

        return list_app_environments_response
