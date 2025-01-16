from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="Token")


@_attrs_define
class Token:
    """
    Attributes:
        jwt (str):
    """

    jwt: str

    def to_dict(self) -> dict[str, Any]:
        jwt = self.jwt

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "jwt": jwt,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        jwt = d.pop("jwt")

        token = cls(
            jwt=jwt,
        )

        return token
