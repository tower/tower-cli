from typing import Any, Dict, Type, TypeVar

import attr

T = TypeVar("T", bound="Token")


@attr.s(auto_attribs=True)
class Token:
    """
    Attributes:
        jwt (str):
    """

    jwt: str

    def to_dict(self) -> Dict[str, Any]:
        jwt = self.jwt

        field_dict: Dict[str, Any] = {}
        field_dict.update(
            {
                "jwt": jwt,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        jwt = d.pop("jwt")

        token = cls(
            jwt=jwt,
        )

        return token
