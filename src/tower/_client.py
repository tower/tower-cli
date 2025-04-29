import os
import time
from typing import Dict, Optional

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
    `run_app` invokes an app based on the configured environment. You can
    supply an optional `environment` override, and an optional dict
    `parameters` to pass into the app.
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
    `wait_for_run` waits for a run to reach a terminal state by polling the
    Tower API every 2 seconds for the latest status. If the app returns a
    terminal status (`exited`, `errored`, `cancelled`, or `crashed`) then this
    function returns.
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
