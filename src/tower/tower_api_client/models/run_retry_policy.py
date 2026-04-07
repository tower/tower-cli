from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="RunRetryPolicy")


@_attrs_define
class RunRetryPolicy:
    """
    Attributes:
        max_retries (int):
        retry_delay_seconds (int):
        use_exponential_backoff (bool):
    """

    max_retries: int
    retry_delay_seconds: int
    use_exponential_backoff: bool

    def to_dict(self) -> dict[str, Any]:
        max_retries = self.max_retries

        retry_delay_seconds = self.retry_delay_seconds

        use_exponential_backoff = self.use_exponential_backoff

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "max_retries": max_retries,
                "retry_delay_seconds": retry_delay_seconds,
                "use_exponential_backoff": use_exponential_backoff,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        max_retries = d.pop("max_retries")

        retry_delay_seconds = d.pop("retry_delay_seconds")

        use_exponential_backoff = d.pop("use_exponential_backoff")

        run_retry_policy = cls(
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            use_exponential_backoff=use_exponential_backoff,
        )

        return run_retry_policy
