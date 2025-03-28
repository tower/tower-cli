import datetime
from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session import Session


T = TypeVar("T", bound="RefreshSessionResponse")


@attr.s(auto_attribs=True)
class RefreshSessionResponse:
    """
    Attributes:
        refreshed_at (datetime.datetime): A timestamp that indicates the last time the session data was refreshed.
        session (Session):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/RefreshSessionResponse.json.
    """

    refreshed_at: datetime.datetime
    session: "Session"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        refreshed_at = self.refreshed_at.isoformat()

        session = self.session.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
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
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.session import Session

        d = src_dict.copy()
        refreshed_at = isoparse(d.pop("refreshed_at"))

        session = Session.from_dict(d.pop("session"))

        schema = d.pop("$schema", UNSET)

        refresh_session_response = cls(
            refreshed_at=refreshed_at,
            session=session,
            schema=schema,
        )

        return refresh_session_response
