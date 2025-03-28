from typing import Any, Dict, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="ErrorDetail")


@attr.s(auto_attribs=True)
class ErrorDetail:
    """
    Attributes:
        location (Union[Unset, str]): Where the error occurred, e.g. 'body.items[3].tags' or 'path.thing-id'
        message (Union[Unset, str]): Error message text
        value (Union[Unset, Any]): The value at the given location
    """

    location: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    value: Union[Unset, Any] = UNSET

    def to_dict(self) -> Dict[str, Any]:
        location = self.location
        message = self.message
        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update({})
        if location is not UNSET:
            field_dict["location"] = location
        if message is not UNSET:
            field_dict["message"] = message
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        location = d.pop("location", UNSET)

        message = d.pop("message", UNSET)

        value = d.pop("value", UNSET)

        error_detail = cls(
            location=location,
            message=message,
            value=value,
        )

        return error_detail
