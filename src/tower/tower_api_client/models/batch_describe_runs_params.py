from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="BatchDescribeRunsParams")


@_attrs_define
class BatchDescribeRunsParams:
    """
    Attributes:
        name (str): The name of the app to describe the run for.
        seq (int): The number of the run to describe.
    """

    name: str
    seq: int

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        seq = self.seq

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "seq": seq,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        seq = d.pop("seq")

        batch_describe_runs_params = cls(
            name=name,
            seq=seq,
        )

        return batch_describe_runs_params
