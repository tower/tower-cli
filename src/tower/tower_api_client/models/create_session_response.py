from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session import Session


T = TypeVar("T", bound="CreateSessionResponse")


@_attrs_define
class CreateSessionResponse:
    """
    Attributes:
        session (Session):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            https://api.tower.dev/v1/schemas/CreateSessionResponse.json.
    """

    session: "Session"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        session = self.session.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
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
        session = Session.from_dict(d.pop("session"))

        schema = d.pop("$schema", UNSET)

        create_session_response = cls(
            session=session,
            schema=schema,
        )

        return create_session_response
