"""
Helpers to ensure users have the correct dependencies installed.

Tower supports optional features that require additional dependencies.
These can be installed using pip:

    pip install "tower[ai]"      # For AI/LLM features
    pip install "tower[iceberg]" # For Apache Iceberg table support
    pip install "tower[all]"     # For all optional features
"""

import importlib.util
from typing import Dict, List, Any, Optional
from importlib import metadata


def is_installed(pkg_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(pkg_name) is not None


def get_package_version(pkg_name: str) -> Optional[str]:
    """Get the version of an installed package, or None if not installed."""
    try:
        return metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        return None


# Define feature dependencies
_feature_dependencies: Dict[str, List[str]] = {
    "ai": ["ollama", "huggingface_hub"],
    "iceberg": ["pyiceberg", "pyarrow", "polars"],
    "dbt": ["dbt"],
}

# Cache for imported modules
_module_cache: Dict[str, Any] = {}

# Define feature modules and their exports
# Format: feature_name: (module_name, [export_names], export_type)
# export_type can be "function" (return specific function) or "module" (return entire module)
_feature_modules: Dict[str, tuple[str, List[str], str]] = {
    "ai": ("_llms", ["llms"], "function"),
    "iceberg": ("_tables", ["tables"], "function"),
    "dbt": ("_dbt", ["dbt"], "function"),
}


def get_available_features() -> Dict[str, Dict[str, Any]]:
    """
    Get information about available optional features.

    Returns:
        A dictionary with feature names as keys and information about each feature:
        - enabled: Whether the feature is available (all dependencies installed)
        - dependencies: List of required packages
        - missing: List of missing packages (if any)
        - installed_versions: Dictionary of installed package versions
        - exports: List of functions/classes provided by this feature
    """
    result = {}

    for feature, deps in _feature_dependencies.items():
        missing = [pkg for pkg in deps if not is_installed(pkg)]
        installed_versions = {
            pkg: get_package_version(pkg)
            for pkg in deps
            if get_package_version(pkg) is not None
        }

        _, exports, _ = _feature_modules.get(feature, ("", [], "function"))

        result[feature] = {
            "enabled": len(missing) == 0,
            "dependencies": deps,
            "missing": missing,
            "installed_versions": installed_versions,
            "exports": exports,
        }

    return result


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if an optional feature is enabled (all dependencies installed).

    Args:
        feature_name: The name of the feature to check

    Returns:
        True if the feature is enabled, False otherwise
    """
    if feature_name not in _feature_dependencies:
        return False

    deps = _feature_dependencies[feature_name]
    return all(is_installed(pkg) for pkg in deps)


def override_get_attr(name: str) -> Any:
    """
    Dynamic attribute lookup for optional features.

    Args:
        name: The attribute name being looked up

    Returns:
        The requested attribute if available

    Raises:
        ImportError: If the attribute requires missing dependencies
        AttributeError: If the attribute doesn't exist
    """
    # Check all feature mappings
    for feature, (module_name, exports, export_type) in _feature_modules.items():
        if name in exports:
            # Check if all dependencies are installed
            deps = _feature_dependencies.get(feature, [])
            missing = [pkg for pkg in deps if not is_installed(pkg)]

            if missing:
                # Show missing dependencies
                raise ImportError(
                    f"This requires the '{feature}' feature and the following dependencies: {deps}.\n"
                    f"You are missing these packages: {missing}\n"
                    f'Install with: pip install "tower[{feature}]"'
                )

            # Check if module is already cached
            if module_name not in _module_cache:
                # Import the module and cache it
                full_module_name = f".{module_name}"
                _module_cache[module_name] = importlib.import_module(
                    full_module_name, __package__
                )

            # Return based on export type
            if export_type == "module":
                # Return the entire module
                return _module_cache[module_name]
            else:
                # Return the specific attribute (function/class) from the module
                return getattr(_module_cache[module_name], name)

    raise AttributeError(f"module 'tower' has no attribute '{name}'")
