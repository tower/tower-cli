from typing import Optional


def schedule_name() -> Optional[str]:
    """
    Retrieve the name of the schedule that invoked this run from the runtime
    environment.

    Returns:
        Optional[str]: The name of the schedule if set, otherwise None.
    """
    return _get_runtime_env_variable("SCHEDULE_NAME", None)


def is_scheduled_run() -> bool:
    """
    Check if the current run is a scheduled run based on environment variables.
    Returns:
        bool: True if it is a scheduled run, otherwise False.
    """
    return schedule_name() is not None


def schedule_id() -> Optional[str]:
    """
    Retrieve the ID of the schedule that invoked this run from the runtime
    environment.

    Returns:
        Optional[str]: The ID of the schedule if set, otherwise None.
    """
    return _get_runtime_env_variable("SCHEDULE_ID", None)


def run_id() -> Optional[str]:
    """
    Retrieve the ID of the current run from the runtime environment.

    Returns:
        Optional[str]: The ID of the run if set, otherwise None.
    """
    return _get_runtime_env_variable("RUN_ID", None)


def run_number() -> Optional[int]:
    """
    Retrieve the number of the current run from the runtime environment.

    Returns:
        Optional[int]: The run number if set, otherwise None.
    """
    run_number_str = _get_runtime_env_variable("RUN_NUMBER", None)
    return int(run_number_str) if run_number_str is not None else None


def hostname() -> Optional[str]:
    """
    Retrieve the hostname of the current run assigned by the runtime
    environment.

    Returns:
        Optional[str]: The hostname if set, otherwise None.
    """
    return _get_env_variable("TOWER__HOST", None)


def port() -> Optional[int]:
    """
    Retrieve the port number assigned to this run by the current runtime
    environment.

    Returns:
        Optional[int]: The port number if set, otherwise None.
    """
    port_str = _get_env_variable("TOWER__PORT", None)
    return int(port_str) if port_str is not None else None


def is_cloud_run() -> bool:
    """
    Check if the current run is executing in the Tower cloud environment.

    Returns:
        bool: True if running in Tower cloud, otherwise False.
    """
    val = _get_runtime_env_variable("IS_TOWER_MANAGED", "")
    return _strtobool(val)


def runner_name() -> str:
    """Retrieve the name of the runner executing this run from the runtime. If the
    name is unknown, an empty string is returned.

    Returns:
        str: The name of the runner or an empty string if unknown.
    """
    return _get_runtime_env_variable("RUNNER_NAME", "")


def runner_id() -> str:
    """
    Retrieve the ID of the runner executing this run from the runtime. If the
    ID is unknown, an empty string is returned.

    Returns:
        str: The ID of the runner or an empty string if unknown.
    """
    return _get_runtime_env_variable("RUNNER_ID", "")


def app_name() -> str:
    """
    Retrieve the name of the app being executed in this run from the runtime.

    Returns:
        str: The name of the app or an empty string if unknown.
    """
    return _get_runtime_env_variable("APP_NAME")


def team_name() -> str:
    """
    Retrieve the name of the team associated with this run from the runtime.

    Returns:
        str: The name of the team or an empty string if unknown.
    """
    return _get_runtime_env_variable("TEAM_NAME", "")


def environment() -> str:
    """
    Retrieve the name of the environment this run is running in.

    Returns:
        str: The name of the environment or an empty string if unknown.
    """
    return _get_runtime_env_variable("ENVIRONMENT_NAME", "")


def is_manual_run() -> bool:
    """
    Check if the current run was manually triggered.

    Returns:
        bool: True if the run was manually triggered, otherwise False.
    """
    val = _get_runtime_env_variable("IS_MANUAL_RUN", "false")
    return _strtobool(val)


def _get_runtime_env_variable(name: str, default: Optional[str] = "") -> Optional[str]:
    """
    Helper function to retrieve a runtime environment variable.

    Args:
        name (str): The name of the runtime environment variable.

    Returns:
        Optional[str]: The value of the runtime environment variable if set, otherwise None.
    """
    return _get_env_variable(f"TOWER__RUNTIME__{name}", default)


def _get_env_variable(var_name: str, default: Optional[str] = "") -> Optional[str]:
    """
    Helper function to retrieve an environment variable.

    Args:
        var_name (str): The name of the environment variable.

    Returns:
        Optional[str]: The value of the environment variable if set, otherwise None.
    """
    import os

    return os.getenv(var_name, default)


def _strtobool(val: str) -> bool:
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")
