from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import run_app
from .tower_api_client.models import RunAppParams


class Client:
    def __init__(self, token: str):
        self.client = AuthenticatedClient(
            base_url="http://localhost:8081",
            token=token,
        )

    def run_app(self, name: str):
        with self.client as client:
            input_body = run_app.RunAppParams(
                environment="default",
                parameters={},
            )

            output: RunAppOutput = run_app.sync(
                name,
                client=client,
                body=input_body
            )
            print(body)
