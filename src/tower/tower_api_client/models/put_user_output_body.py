from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="PutUserOutputBody")


@_attrs_define
class PutUserOutputBody:
    """
    Attributes:
        user (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object.
    """

    user: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        schema = self.schema

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "user": user,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.user import User

        d = src_dict.copy()
        user = User.from_dict(d.pop("user"))

        schema = d.pop("$schema", UNSET)

        put_user_output_body = cls(
            user=user,
            schema=schema,
        )

        return put_user_output_body
