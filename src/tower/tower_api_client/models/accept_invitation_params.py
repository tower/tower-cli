from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="AcceptInvitationParams")


@attr.s(auto_attribs=True)
class AcceptInvitationParams:
    """
    Attributes:
        code (str): The invitation code to accept
        schema (Union[Unset, str]): A URL to the JSON Schema for this object. Example:
            http://localhost:8081/v1/schemas/AcceptInvitationParams.json.
    """

    code: str
    schema: Union[Unset, str] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        code = self.code
        schema = self.schema

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "code": code,
            }
        )
        if schema is not UNSET:
            field_dict["$schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        code = d.pop("code")

        schema = d.pop("$schema", UNSET)

        accept_invitation_params = cls(
            code=code,
            schema=schema,
        )

        return accept_invitation_params
