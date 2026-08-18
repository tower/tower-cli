from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.run import Run
    from ..models.run_links import RunLinks


T = TypeVar("T", bound="RunAndLinks")


@_attrs_define
class RunAndLinks:
    """
    Attributes:
        links (RunLinks):
        run (Run):
    """

    links: RunLinks
    run: Run

    def to_dict(self) -> dict[str, Any]:
        links = self.links.to_dict()

        run = self.run.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "$links": links,
                "run": run,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run import Run
        from ..models.run_links import RunLinks

        d = dict(src_dict)
        links = RunLinks.from_dict(d.pop("$links"))

        run = Run.from_dict(d.pop("run"))

        run_and_links = cls(
            links=links,
            run=run,
        )

        return run_and_links
