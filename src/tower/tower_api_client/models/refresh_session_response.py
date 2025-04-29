import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session import Session


T = TypeVar("T", bound="RefreshSessionResponse")


@_attrs_define
class RefreshSessionResponse:
    """
    Attributes:
        refreshed_at (datetime.datetime): A timestamp that indicates the last time the session data was refreshed.
        session (Session):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/RefreshSessionResponse.json.
    """

    refreshed_at: datetime.datetime
    session: "Session"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        refreshed_at = self.refreshed_at.isoformat()

        session = self.session.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "refreshed_at": refreshed_at,
                "session": session,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session import Session

        d = dict(src_dict)
        refreshed_at = isoparse(d.pop("refreshed_at"))

        session = Session.from_dict(d.pop("session"))

        schema = d.pop("$schema", UNSET)

        refresh_session_response = cls(
            refreshed_at=refreshed_at,
            session=session,
            schema=schema,
        )

        return refresh_session_response
