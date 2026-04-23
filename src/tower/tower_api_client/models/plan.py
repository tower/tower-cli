from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.feature import Feature


T = TypeVar("T", bound="Plan")


@_attrs_define
class Plan:
    """
    Attributes:
        base_plan_name (str):
        created_at (datetime.datetime):
        features (list[Feature]):
        id (str):
        start_at (datetime.datetime):
        end_at (datetime.datetime | Unset):
        extras (list[Feature] | Unset):
    """

    base_plan_name: str
    created_at: datetime.datetime
    features: list[Feature]
    id: str
    start_at: datetime.datetime
    end_at: datetime.datetime | Unset = UNSET
    extras: list[Feature] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        base_plan_name = self.base_plan_name

        created_at = self.created_at.isoformat()

        features = []
        for features_item_data in self.features:
            features_item = features_item_data.to_dict()
            features.append(features_item)

        id = self.id

        start_at = self.start_at.isoformat()

        end_at: str | Unset = UNSET
        if not isinstance(self.end_at, Unset):
            end_at = self.end_at.isoformat()

        extras: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.extras, Unset):
            extras = []
            for extras_item_data in self.extras:
                extras_item = extras_item_data.to_dict()
                extras.append(extras_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "base_plan_name": base_plan_name,
                "created_at": created_at,
                "features": features,
                "id": id,
                "start_at": start_at,
            }
        )
        if end_at is not UNSET:
            field_dict["end_at"] = end_at
        if extras is not UNSET:
            field_dict["extras"] = extras

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.feature import Feature

        d = dict(src_dict)
        base_plan_name = d.pop("base_plan_name")

        created_at = isoparse(d.pop("created_at"))

        features = []
        _features = d.pop("features")
        for features_item_data in _features:
            features_item = Feature.from_dict(features_item_data)

            features.append(features_item)

        id = d.pop("id")

        start_at = isoparse(d.pop("start_at"))

        _end_at = d.pop("end_at", UNSET)
        end_at: datetime.datetime | Unset
        if isinstance(_end_at, Unset):
            end_at = UNSET
        else:
            end_at = isoparse(_end_at)

        _extras = d.pop("extras", UNSET)
        extras: list[Feature] | Unset = UNSET
        if _extras is not UNSET:
            extras = []
            for extras_item_data in _extras:
                extras_item = Feature.from_dict(extras_item_data)

                extras.append(extras_item)

        plan = cls(
            base_plan_name=base_plan_name,
            created_at=created_at,
            features=features,
            id=id,
            start_at=start_at,
            end_at=end_at,
            extras=extras,
        )

        return plan
