"""
Tower: A compute platform for modern data projects.

This package provides tools for interacting with the Tower platform,
including running apps locally or in the Tower cloud.

Optional features:
- AI/LLM support: Install with `pip install "tower[ai]"`
- Apache Iceberg support: Install with `pip install "tower[iceberg]"`
- dbt Core support: Install with `pip install "tower[dbt]"`
- All features: Install with `pip install "tower[all]"`
"""

from typing import TYPE_CHECKING

from ._client import (
    run_app,
    wait_for_run,
    wait_for_runs,
)

from ._features import override_get_attr, get_available_features, is_feature_enabled

if TYPE_CHECKING:
    from ._tables import tables as tables
    from ._llms import llms as llms
    from ._dbt import dbt as dbt


def __getattr__(name: str):
    """
    Dynamic attribute lookup for optional features.

    This allows Tower to lazily load optional dependencies only when
    their features are actually used.
    """
    return override_get_attr(name)
