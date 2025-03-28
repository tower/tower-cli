from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="AcceptInvitationResponse")


@attr.s(auto_attribs=True)
class AcceptInvitationResponse:
    """
    Attributes:
        user (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/AcceptInvitationResponse.json.
    """

    user: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        user = self.user.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "user": user,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user import User

        d = src_dict.copy()
        user = User.from_dict(d.pop("user"))

        schema = d.pop("$schema", UNSET)

        accept_invitation_response = cls(
            user=user,
            schema=schema,
        )

        return accept_invitation_response
