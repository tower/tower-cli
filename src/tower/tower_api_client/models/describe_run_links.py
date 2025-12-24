from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="DescribeRunLinks")


@_attrs_define
class DescribeRunLinks:
    """
    Attributes:
        next_ (Union[None, str]): The URL of the next run, if any.
        prev (Union[None, str]): The URL of the previous run, if any.
        self_ (str): The URL of this run.
    """

    next_: Union[None, str]
    prev: Union[None, str]
    self_: str

    def to_dict(self) -> dict[str, Any]:
        next_: Union[None, str]
        next_ = self.next_

        prev: Union[None, str]
        prev = self.prev

        self_ = self.self_

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "next": next_,
                "prev": prev,
                "self": self_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_next_(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        next_ = _parse_next_(d.pop("next"))

        def _parse_prev(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        prev = _parse_prev(d.pop("prev"))

        self_ = d.pop("self")

        describe_run_links = cls(
            next_=next_,
            prev=prev,
            self_=self_,
        )

        return describe_run_links
