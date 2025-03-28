from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session import Session


T = TypeVar("T", bound="CreateSessionResponse")


@attr.s(auto_attribs=True)
class CreateSessionResponse:
    """
    Attributes:
        session (Session):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/CreateSessionResponse.json.
    """

    session: "Session"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        session = self.session.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
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
        session = Session.from_dict(d.pop("session"))

        schema = d.pop("$schema", UNSET)

        create_session_response = cls(
            session=session,
            schema=schema,
        )

        return create_session_response
