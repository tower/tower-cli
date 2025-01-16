from tower_api_client import AuthenticatedClient
from tower_api_client.models import PostAppRunsOutputBody
from tower_api_client.api.default import post_app_run

class Client:
    def __init__(self, token: str):
        self.client = AuthenticatedClient(
                base_url="http://localhost:8081", 
                token=token,
        )

    def run_app(self, name: str):
        with self.client as client:
            input_body = post_app_run.PostAppRunsInputBody(
                    environment="default",
                    parameters={})

            body: PostAppRunsOutputBody = post_app_run.sync(name, client=client, body=input_body)
            print(body)

