from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
    from ..models.parameter import Parameter


T = TypeVar("T", bound="AppVersion")


@attr.s(auto_attribs=True)
class AppVersion:
    """
    Attributes:
        parameters (List['Parameter']):
        version (str):
    """

    parameters: List["Parameter"]
    version: str

    def to_dict(self) -> Dict[str, Any]:
        parameters = []
        for parameters_item_data in self.parameters:
            parameters_item = parameters_item_data.to_dict()

            parameters.append(parameters_item)

        version = self.version

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "parameters": parameters,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.parameter import Parameter

        d = src_dict.copy()
        parameters = []
        _parameters = d.pop("parameters")
        for parameters_item_data in _parameters:
            parameters_item = Parameter.from_dict(parameters_item_data)

            parameters.append(parameters_item)

        version = d.pop("version")

        app_version = cls(
            parameters=parameters,
            version=version,
        )

        return app_version
