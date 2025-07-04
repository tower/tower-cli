from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="AppStatistics")


@_attrs_define
class AppStatistics:
    """
    Attributes:
        all_apps (int):
        disabled_apps (int):
        healthy_apps (int):
        running_apps (int):
    """

    all_apps: int
    disabled_apps: int
    healthy_apps: int
    running_apps: int

    def to_dict(self) -> dict[str, Any]:
        all_apps = self.all_apps

        disabled_apps = self.disabled_apps

        healthy_apps = self.healthy_apps

        running_apps = self.running_apps

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "all_apps": all_apps,
                "disabled_apps": disabled_apps,
                "healthy_apps": healthy_apps,
                "running_apps": running_apps,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        all_apps = d.pop("all_apps")

        disabled_apps = d.pop("disabled_apps")

        healthy_apps = d.pop("healthy_apps")

        running_apps = d.pop("running_apps")

        app_statistics = cls(
            all_apps=all_apps,
            disabled_apps=disabled_apps,
            healthy_apps=healthy_apps,
            running_apps=running_apps,
        )

        return app_statistics
