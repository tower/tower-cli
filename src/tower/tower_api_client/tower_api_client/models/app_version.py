from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.parameter import Parameter


T = TypeVar("T", bound="AppVersion")


@_attrs_define
class AppVersion:
    """
    Attributes:
        parameters (Union[None, list['Parameter']]):
        version (str):
    """

    parameters: Union[None, list["Parameter"]]
    version: str

    def to_dict(self) -> dict[str, Any]:
        parameters: Union[None, list[dict[str, Any]]]
        if isinstance(self.parameters, list):
            parameters = []
            for parameters_type_0_item_data in self.parameters:
                parameters_type_0_item = parameters_type_0_item_data.to_dict()
                parameters.append(parameters_type_0_item)

        else:
            parameters = self.parameters

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "parameters": parameters,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.parameter import Parameter

        d = src_dict.copy()

        def _parse_parameters(data: object) -> Union[None, list["Parameter"]]:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                parameters_type_0 = []
                _parameters_type_0 = data
                for parameters_type_0_item_data in _parameters_type_0:
                    parameters_type_0_item = Parameter.from_dict(parameters_type_0_item_data)

                    parameters_type_0.append(parameters_type_0_item)

                return parameters_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, list["Parameter"]], data)

        parameters = _parse_parameters(d.pop("parameters"))

        version = d.pop("version")

        app_version = cls(
            parameters=parameters,
            version=version,
        )

        return app_version
