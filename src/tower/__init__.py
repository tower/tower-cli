"""
Tower: A compute platform for modern data projects.

This package provides tools for interacting with the Tower platform,
including running apps locally or in the Tower cloud.

Optional features:
- AI/LLM support: Install with `pip install "tower[ai]"`
- Apache Iceberg support: Install with `pip install "tower[iceberg]"`
- All features: Install with `pip install "tower[all]"`
"""

from ._client import (
    run_app,
    wait_for_run,
    wait_for_runs,
)

from ._features import override_get_attr, get_available_features, is_feature_enabled


def __getattr__(name: str) -> any:
    """
    Dynamic attribute lookup for optional features.

    This allows Tower to lazily load optional dependencies only when
    their features are actually used.
    """
    return override_get_attr(name)
