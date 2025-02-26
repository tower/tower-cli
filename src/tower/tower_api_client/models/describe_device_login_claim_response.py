from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="DescribeDeviceLoginClaimResponse")


@attr.s(auto_attribs=True)
class DescribeDeviceLoginClaimResponse:
    """
    Attributes:
        token (str): The JWT token.
        user (User):
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/DescribeDeviceLoginClaimResponse.json.
    """

    token: str
    user: "User"
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        token = self.token
        user = self.user.to_dict()

        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "token": token,
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
        token = d.pop("token")

        user = User.from_dict(d.pop("user"))

        schema = d.pop("$schema", UNSET)

        describe_device_login_claim_response = cls(
            token=token,
            user=user,
            schema=schema,
        )

        return describe_device_login_claim_response
