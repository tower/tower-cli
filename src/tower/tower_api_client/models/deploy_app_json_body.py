from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DeployAppJsonBody")


@_attrs_define
class DeployAppJsonBody:
    """
    Example:
        {'source_uri': 'https://github.com/tower/tower-examples/tree/main/01-hello-world'}

    Attributes:
        source_uri (str): GitHub repository URL for deploying from source
    """

    source_uri: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_uri = self.source_uri

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_uri": source_uri,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source_uri = d.pop("source_uri")

        deploy_app_json_body = cls(
            source_uri=source_uri,
        )

        deploy_app_json_body.additional_properties = d
        return deploy_app_json_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
