import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.features import Features


T = TypeVar("T", bound="Plan")


@_attrs_define
class Plan:
    """
    Attributes:
        account_id (str):
        base_plan_name (str):
        created_at (datetime.datetime):
        features (Features):
        id (str):
        start_at (datetime.datetime):
        status (str):
        end_at (Union[Unset, datetime.datetime]):
        extras (Union[Unset, Features]):
    """

    account_id: str
    base_plan_name: str
    created_at: datetime.datetime
    features: "Features"
    id: str
    start_at: datetime.datetime
    status: str
    end_at: Union[Unset, datetime.datetime] = UNSET
    extras: Union[Unset, "Features"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        account_id = self.account_id

        base_plan_name = self.base_plan_name

        created_at = self.created_at.isoformat()

        features = self.features.to_dict()

        id = self.id

        start_at = self.start_at.isoformat()

        status = self.status

        end_at: Union[Unset, str] = UNSET
        if not isinstance(self.end_at, Unset):
            end_at = self.end_at.isoformat()

        extras: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.extras, Unset):
            extras = self.extras.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "account_id": account_id,
                "base_plan_name": base_plan_name,
                "created_at": created_at,
                "features": features,
                "id": id,
                "start_at": start_at,
                "status": status,
            }
        )
        if end_at is not UNSET:
            field_dict["end_at"] = end_at
        if extras is not UNSET:
            field_dict["extras"] = extras

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.features import Features

        d = dict(src_dict)
        account_id = d.pop("account_id")

        base_plan_name = d.pop("base_plan_name")

        created_at = isoparse(d.pop("created_at"))

        features = Features.from_dict(d.pop("features"))

        id = d.pop("id")

        start_at = isoparse(d.pop("start_at"))

        status = d.pop("status")

        _end_at = d.pop("end_at", UNSET)
        end_at: Union[Unset, datetime.datetime]
        if isinstance(_end_at, Unset):
            end_at = UNSET
        else:
            end_at = isoparse(_end_at)

        _extras = d.pop("extras", UNSET)
        extras: Union[Unset, Features]
        if isinstance(_extras, Unset):
            extras = UNSET
        else:
            extras = Features.from_dict(_extras)

        plan = cls(
            account_id=account_id,
            base_plan_name=base_plan_name,
            created_at=created_at,
            features=features,
            id=id,
            start_at=start_at,
            status=status,
            end_at=end_at,
            extras=extras,
        )

        return plan
