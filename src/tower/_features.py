"""
Helpers to ensure users have the correct dependencies installed
"""

import importlib.util


def is_installed(pkg_name: str) -> bool:
    return importlib.util.find_spec(pkg_name) is not None


enabled_features = {
    "ai": is_installed("ollama"),
    "iceberg": is_installed("pyiceberg"),
}
