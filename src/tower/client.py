import os
from typing import Any, Dict, Optional

from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import run_app as run_app_api
from .tower_api_client.models import (
    RunAppParamsParameters,
    RunAppParams,
    RunAppResponse,
)

def _env_client() -> AuthenticatedClient:
    api_key = os.getenv("TOWER_API_KEY")
    return AuthenticatedClient(
        verify_ssl=False,
        base_url='http://localhost:8081/v1',
        token=api_key,
        auth_header_name='X-API-Key',
        prefix='',
    )


def run_app(name: str):
    client = _env_client()
    params = RunAppParamsParameters()

    input_body = RunAppParams(
        environment="default",
        parameters=params,
    )

    output: RunAppResponse = run_app_api.sync(
        name=name,
        client=client,
        json_body=input_body
    )
    print(output)
