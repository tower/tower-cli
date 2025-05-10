import os
import time
from typing import List, Dict, Optional

from ._context import TowerContext
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

# WAIT_TIMEOUT is the amount of time to wait between requests when polling the
# Tower API.
WAIT_TIMEOUT = 2

# DEFAULT_TOWER_URL is the default tower URL to use when connecting back to
# Tower.
DEFAULT_TOWER_URL = "https://api.tower.dev"

# DEFAULT_TOWER_ENVIRONMENT is the default environment to use when running an
# app somewhere.
DEFAULT_TOWER_ENVIRONMENT = "default"


def _env_client(ctx: TowerContext) -> AuthenticatedClient:
    tower_url = ctx.tower_url

    if not tower_url.endswith("/v1"):
        if tower_url.endswith("/"):
            tower_url += "v1"
        else:
            tower_url += "/v1"

    return AuthenticatedClient(
        verify_ssl=False,
        base_url=tower_url,
        token=ctx.api_key,
        auth_header_name="X-API-Key",
        prefix="",
    )


def run_app(
    slug: str,
    environment: Optional[str] = None,
    parameters: Optional[Dict[str, str]] = None,
) -> Run:
    """
    Run a Tower application with specified parameters and environment.

    This function initiates a new run of a Tower application identified by its slug.
    The run can be configured with an optional environment override and runtime parameters.
    If no environment is specified, the default environment from the Tower context is used.

    Args:
        slug (str): The unique identifier of the application to run.
        environment (Optional[str]): The environment to run the application in.
            If not provided, uses the default environment from the Tower context.
        parameters (Optional[Dict[str, str]]): A dictionary of key-value pairs
            to pass as parameters to the application run.

    Returns:
        Run: A Run object containing information about the initiated application run,
            including the app_slug and run number.

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

    output: Optional[Union[ErrorModel, RunAppResponse]] = run_app_api.sync(
        slug=slug, client=client, body=input_body
    )

    if output is None:
        raise RuntimeError("Error running app")
    else:
        if isinstance(output, ErrorModel):
            raise RuntimeError(f"Error running app: {output.title}")
        else:
            return output.run


def wait_for_run(run: Run) -> None:
    """
    Wait for a Tower app run to reach a terminal state by polling the Tower API.

    This function continuously polls the Tower API every 2 seconds (defined by WAIT_TIMEOUT)
    to check the status of the specified run. The function returns when the run reaches
    any of the following terminal states:
    - exited: The run completed successfully
    - failed: The run failed during execution
    - canceled: The run was manually canceled
    - errored: The run encountered an error

    Args:
        run (Run): The Run object containing the app_slug and number of the run to monitor.

    Returns:
        None: This function does not return any value.

    Raises:
        RuntimeError: If there is an error fetching the run status from the Tower API
            or if the API returns an error response.
    """
    ctx = TowerContext.build()
    client = _env_client(ctx)

    while True:
        output: Optional[Union[DescribeRunResponse, ErrorModel]] = describe_run_api.sync(
            slug=run.app_slug,
            seq=run.number,
            client=client
        )

        if output is None:
            raise RuntimeError("Error fetching run")
        else:
            if isinstance(output, ErrorModel):
                raise RuntimeError(f"Error fetching run: {output.title}")
            else:
                desc = output.run

                if desc.status == "exited":
                    return
                elif desc.status == "failed":
                    return
                elif desc.status == "canceled":
                    return
                elif desc.status == "errored":
                    return
                else:
                    time.sleep(WAIT_TIMEOUT)


def wait_for_runs(runs: List[Run]) -> None:
    """
    `wait_for_runs` waits for a list of runs to reach a terminal state by
    polling the Tower API every 2 seconds for the latest status. If any of the
    runs return a terminal status (`exited`, `errored`, `cancelled`, or
    `crashed`) then this function returns.

    Args:
        runs (List[Run]): A list of Run objects to monitor.

    Returns:
        None: This function does not return any value.

    Raises:
        RuntimeError: If there is an error fetching the run status or if any
            of the runs fail.
    """
    for run in runs:
        wait_for_run(run)
