import os
import time
import httpx
from typing import List, Dict, Optional

from ._context import TowerContext
from .exceptions import (
    AppNotFoundError,
    NotFoundException,
    UnauthorizedException,
    UnknownException,
    UnhandledRunStateException,
    RunFailedError,
    TimeoutException,
)

from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import describe_run as describe_run_api
from .tower_api_client.api.default import run_app as run_app_api
from .tower_api_client.models import (
    DescribeRunResponse,
    Run,
    RunAppParams,
    RunAppParamsParameters,
    RunAppResponse,
)
from .tower_api_client.models.error_model import ErrorModel
from .tower_api_client.errors import UnexpectedStatus

# WAIT_TIMEOUT is the amount of time to wait between requests when polling the
# Tower API.
WAIT_TIMEOUT = 2

# DEFAULT_TOWER_URL is the default tower URL to use when connecting back to
# Tower.
DEFAULT_TOWER_URL = "https://api.tower.dev"

# DEFAULT_TOWER_ENVIRONMENT is the default environment to use when running an
# app somewhere.
DEFAULT_TOWER_ENVIRONMENT = "default"

# DEFAULT_NUM_TIMEOUT_RETRIES is the number of times to retry querying the Tower
# API before we just give up entirely.
DEFAULT_NUM_TIMEOUT_RETRIES = 5


def run_app(
    name: str,
    environment: Optional[str] = None,
    parameters: Optional[Dict[str, str]] = None,
) -> Run:
    """
    Run a Tower application with specified parameters and environment.

    This function initiates a new run of a Tower application identified by its name.
    The run can be configured with an optional environment override and runtime parameters.
    If no environment is specified, the default environment from the Tower context is used.

    Args:
        name (str): The unique identifier of the application to run.
        environment (Optional[str]): The environment to run the application in.
            If not provided, uses the default environment from the Tower context.
        parameters (Optional[Dict[str, str]]): A dictionary of key-value pairs
            to pass as parameters to the application run.

    Returns:
        Run: A Run object containing information about the initiated application run,
            including the app_name and run number.

    Raises:
        RuntimeError: If there is an error initiating the run or if the Tower API
            returns an error response.
    """
    ctx = TowerContext.build()
    client = _env_client(ctx)
    run_params = RunAppParamsParameters()

    if not environment:
        environment = ctx.environment

    if parameters:
        run_params = RunAppParamsParameters.from_dict(parameters)

    input_body = RunAppParams(
        environment=environment,
        parameters=run_params,
    )

    try:
        output: Optional[Union[ErrorModel, RunAppResponse]] = run_app_api.sync(
            name=name, client=client, body=input_body
        )

        if output is None:
            raise RuntimeError("Error running app")
        else:
            if isinstance(output, ErrorModel):
                raise RuntimeError(f"Error running app: {output.title}")
            else:
                return output.run
    except UnexpectedStatus as e:
        # Raise an AppNotFoundError here if the app was, indeed, not found.
        if e.status_code == 404:
            raise AppNotFoundError(name)
        else:
            raise UnknownException(
                f"Unexpected status code {e.status_code} when running app {name}"
            )


def wait_for_run(
    run: Run,
    timeout: Optional[float] = 86_400.0,  # one day
    raise_on_failure: bool = False,
) -> Run:
    """
    Wait for a Tower app run to reach a terminal state by polling the Tower API.

    This function continuously polls the Tower API every 2 seconds (defined by WAIT_TIMEOUT)
    to check the status of the specified run. The function returns when the run reaches
    a terminal state (exited, errored, cancelled, or crashed).

    Args:
        run (Run): The Run object containing the app_name and number of the run to monitor.
        timeout (Optional[float]): Maximum time to wait in seconds before raising a
            TimeoutException. Defaults to one day (86,400 seconds).
        raise_on_failure (bool): If True, raises a RunFailedError when the run fails.
            If False, returns the failed run object. Defaults to False.

    Returns:
        Run: The final state of the run after completion or failure.

    Raises:
        TimeoutException: If the specified timeout is reached before the run completes.
        RunFailedError: If raise_on_failure is True and the run fails.
        UnhandledRunStateException: If the run enters an unexpected state.
        UnknownException: If there are persistent problems communicating with the Tower API.
        NotFoundException: If the run cannot be found.
        UnauthorizedException: If the API key is invalid or unauthorized.
    """
    ctx = TowerContext.build()
    retries = 0

    # We use this to track the timeout, if one is defined.
    start_time = time.time()

    while True:
        # We check for a timeout at the top of the loop because we want to
        # avoid waiting unnecessarily for the timeout hitting the Tower API if
        # we've enounctered some sort of operational problem there.
        if timeout is not None:
            if _time_since(start_time) > timeout:
                raise TimeoutException(_time_since(start_time))

        # We time this out to avoid waiting forever on the API.
        try:
            desc = _check_run_status(ctx, run, timeout=2.0)
            retries = 0

            if _is_successful_run(desc):
                return desc
            elif _is_failed_run(desc):
                if raise_on_failure:
                    raise RunFailedError(desc.app_name, desc.number, desc.status)
                else:
                    return desc

            elif _is_run_awaiting_completion(desc):
                time.sleep(WAIT_TIMEOUT)
            else:
                raise UnhandledRunStateException(desc.status)
        except TimeoutException:
            # timed out in the API, we want to keep trying this for a while
            # (assuming we didn't hit the global timeout limit) until we give
            # up entirely.
            retries += 1

            if retries >= DEFAULT_NUM_TIMEOUT_RETRIES:
                raise UnknownException("There was a problem with the Tower API.")


def wait_for_runs(
    runs: List[Run],
    timeout: Optional[float] = 86_400.0,  # one day
    raise_on_failure: bool = False,
) -> tuple[List[Run], List[Run]]:
    """
    Wait for multiple Tower app runs to reach terminal states by polling the Tower API.

    This function continuously polls the Tower API every 2 seconds (defined by WAIT_TIMEOUT)
    to check the status of all specified runs. The function returns when all runs reach
    terminal states (`exited`, `errored`, `cancelled`, or `crashed`).

    Args:
        runs (List[Run]): A list of Run objects to monitor.
        timeout (Optional[float]): Maximum time to wait in seconds before raising a
            TimeoutException. Defaults to one day (86,400 seconds).
        raise_on_failure (bool): If True, raises a RunFailedError when any run fails.
            If False, failed runs are returned in the failed_runs list. Defaults to False.

    Returns:
        tuple[List[Run], List[Run]]: A tuple containing two lists:
            - successful_runs: List of runs that completed successfully (status: 'exited')
            - failed_runs: List of runs that failed (status: 'crashed', 'cancelled', or 'errored')

    Raises:
        TimeoutException: If the specified timeout is reached before all runs complete.
        RunFailedError: If raise_on_failure is True and any run fails.
        UnhandledRunStateException: If a run enters an unexpected state.
        UnknownException: If there are persistent problems communicating with the Tower API.
        NotFoundException: If any run cannot be found.
        UnauthorizedException: If the API key is invalid or unauthorized.
    """
    ctx = TowerContext.build()
    retries = 0

    # We use this to track the timeout, if one is defined.
    start_time = time.time()

    awaiting_runs = runs
    successful_runs = []
    failed_runs = []

    while len(awaiting_runs) > 0:
        run = awaiting_runs.pop(0)

        # Check the overall timeout at the top of the loop in case we've
        # spent a load of time deeper inside the loop on reties, etc.
        if timeout is not None:
            if _time_since(start_time) > timeout:
                raise TimeoutException(_time_since(start_time))

        try:
            desc = _check_run_status(ctx, run, timeout=2.0)
            retries = 0

            if _is_successful_run(desc):
                successful_runs.append(desc)
            elif _is_failed_run(desc):
                if raise_on_failure:
                    raise RunFailedError(desc.app_name, desc.number, desc.status)
                else:
                    failed_runs.append(desc)

            elif _is_run_awaiting_completion(desc):
                time.sleep(WAIT_TIMEOUT)

                # We need to re-add this run to the list so we check it again
                # in the future. We add it to the back since we took it off the
                # front, effectively moving to the next run.
                awaiting_runs.append(desc)
            else:
                raise UnhandledRunStateException(desc.status)
        except TimeoutException:
            # timed out in the API, we want to keep trying this for a while
            # (assuming we didn't hit the global timeout limit) until we give
            # up entirely.
            retries += 1

            if retries >= DEFAULT_NUM_TIMEOUT_RETRIES:
                raise UnknownException("There was a problem with the Tower API.")
            else:
                # Add the item back on the list for retry later on.
                awaiting_runs.append(run)

    return (successful_runs, failed_runs)


def _is_failed_run(run: Run) -> bool:
    """
    Check if the given run has failed.

    Args:
        run (Run): The Run object containing the status to check.

    Returns:
        bool: True if the run has failed, False otherwise.
    """
    return run.status in ["crashed", "cancelled", "errored"]


def _is_successful_run(run: Run) -> bool:
    """
    Check if a given run was successful.

    Args:
        run (Run): The Run object containing the status to check.

    Returns:
        bool: True if the run was successful, False otherwise.
    """
    return run.status in ["exited"]


def _is_run_awaiting_completion(run: Run) -> bool:
    """
    Check if a given run is either running or expected to run in the near future.

    Args:
       run (Run): The Run object containing the status to check.

    Returns:
        bool: True if the run is awaiting run or currently running, False otherwise.
    """
    return run.status in ["pending", "scheduled", "running"]


def _env_client(
    ctx: TowerContext, timeout: Optional[float] = None
) -> AuthenticatedClient:
    tower_url = ctx.tower_url

    if not tower_url.endswith("/v1"):
        if tower_url.endswith("/"):
            tower_url += "v1"
        else:
            tower_url += "/v1"

    if ctx.jwt is not None:
        token = ctx.jwt
        auth_header_name = "Authorization"
        prefix = "Bearer"
    else:
        token = ctx.api_key
        auth_header_name = "X-API-Key"
        prefix = ""

    return AuthenticatedClient(
        verify_ssl=False,
        base_url=tower_url,
        token=token,
        auth_header_name=auth_header_name,
        prefix=prefix,
        timeout=timeout,
        raise_on_unexpected_status=True,
    )


def _time_since(start_time: float) -> float:
    return time.time() - start_time


def _check_run_status(
    ctx: TowerContext,
    run: Run,
    timeout: Optional[float] = 2.0,  # one day
) -> Run:
    client = _env_client(ctx, timeout=timeout)

    try:
        output: Optional[Union[DescribeRunResponse, ErrorModel]] = (
            describe_run_api.sync(name=run.app_name, seq=run.number, client=client)
        )

        if output is None:
            raise UnknownException("Failed to fetch run")
        elif isinstance(output, ErrorModel):
            # If it was a 404 error, that means that we couldn't find this
            # app for some reason. This is really only relevant on the
            # first time that we check--if we could find the run, but then
            # suddenly couldn't that's a really big problem I'd say.
            if output.status == 404:
                raise NotFoundException(output.detail)
            elif output.status == 401:
                # NOTE: Most of the time, this shouldn't happen?
                raise UnauthorizedException(output.detail)
            else:
                raise UnknownException(output.detail)
        else:
            # There was a run object, so let's return that.
            return output.run
    except httpx.TimeoutException:
        # If we received a timeout from the API then we should raise our own
        # timeout type.
        raise TimeoutException(timeout)
