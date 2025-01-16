from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetAppEnvironmentsOutputBody")


@_attrs_define
class GetAppEnvironmentsOutputBody:
    """
    Attributes:
        environments (Union[None, list[str]]):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    environments: Union[None, list[str]]
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        environments: Union[None, list[str]]
        if isinstance(self.environments, list):
            environments = self.environments

        else:
            environments = self.environments

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "environments": environments,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_environments(data: object) -> Union[None, list[str]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                environments_type_0 = cast(list[str], data)

                return environments_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list[str]], data)

        environments = _parse_environments(d.pop("environments"))

        schema = d.pop("$schema", UNSET)

        get_app_environments_output_body = cls(
            environments=environments,
            schema=schema,
        )

        return get_app_environments_output_body
