import os
from typing import Any, Dict, Optional

from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import run_app as run_app_api
from .tower_api_client.models import (
    RunAppParamsParameters,
    RunAppParams,
    RunAppResponse,
)

# DEFAULT_TOWER_URL is the default tower URL to use when connecting back to
# Tower.
DEFAULT_TOWER_URL = "https://api.tower.dev"

# DEFAULT_TOWER_ENVIRONMENT is the default environment to use when running an
# app somewhere.
DEFAULT_TOWER_ENVIRONMENT = "default"

class Run:
    def __init__(self, app_name: str, number: int):
        self.app_name = name
        self.number = number

def _env_client() -> AuthenticatedClient:
    api_key = os.getenv("TOWER_API_KEY")
    tower_url = os.getenv("TOWER_URL", DEFAULT_TOWER_URL)

    if not tower_url.endswith('/v1'):
        if tower_url.endswith('/'):
            tower_url += 'v1'
        else:
            tower_url += '/v1'

    return AuthenticatedClient(
        verify_ssl=False,
        base_url=tower_url,
        token=api_key,
        auth_header_name='X-API-Key',
        prefix='',
    )

def run_app(
    name: str,
    environment: Optional[str] = None,
    params: Optional[Dict[str, str]] = None
) -> None:
    client = _env_client()
    run_params = RunAppParamsParameters()

    if not environment:
        environment = os.getenv("TOWER_ENVIRONMENT", DEFAULT_TOWER_ENVIRONMENT)

    if params:
        run_params.update(params)

    input_body = RunAppParams(
        environment=environment,
        parameters=run_params,
    )

    output: Optional[RunAppResponse] = run_app_api.sync(
        name=name,
        client=client,
        json_body=input_body
    )
    print("Output:", output)
