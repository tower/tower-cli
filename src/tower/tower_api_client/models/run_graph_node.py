from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.run_graph_run_id import RunGraphRunID


T = TypeVar("T", bound="RunGraphNode")


@_attrs_define
class RunGraphNode:
    """
    Attributes:
        id (RunGraphRunID):
        parent_id (RunGraphRunID):
    """

    id: "RunGraphRunID"
    parent_id: "RunGraphRunID"

    def to_dict(self) -> dict[str, Any]:
        id = self.id.to_dict()

        parent_id = self.parent_id.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "id": id,
                "parent_id": parent_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_graph_run_id import RunGraphRunID

        d = dict(src_dict)
        id = RunGraphRunID.from_dict(d.pop("id"))

        parent_id = RunGraphRunID.from_dict(d.pop("parent_id"))

        run_graph_node = cls(
            id=id,
            parent_id=parent_id,
        )

        return run_graph_node
