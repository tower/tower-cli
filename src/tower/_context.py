import os


class TowerContext:
    def __init__(
        self,
        tower_url: str,
        environment: str,
        api_key: str = None,
        inference_router: str = None,
        inference_router_api_key: str = None,
        inference_provider: str = None,
        jwt: str = None,
    ):
        self.tower_url = tower_url
        self.environment = environment
        self.api_key = api_key
        self.jwt = jwt
        self.inference_router = inference_router
        self.inference_router_api_key = inference_router_api_key
        self.inference_provider = inference_provider

    def is_local(self) -> bool:
        if self.environment is None or self.environment == "":
            return True
        elif self.environment == "local":
            return True
        else:
            return False

    @classmethod
    def build(cls):
        tower_url = os.getenv("TOWER_URL", "https://api.tower.dev")
        tower_environment = os.getenv("TOWER_ENVIRONMENT", "default")
        tower_api_key = os.getenv("TOWER_API_KEY")
        tower_jwt = os.getenv("TOWER_JWT")

        # Replaces the deprecated hugging_face_provider and hugging_face_api_key
        inference_router = os.getenv("TOWER_INFERENCE_ROUTER")
        inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
        inference_provider = os.getenv("TOWER_INFERENCE_PROVIDER")

        return cls(
            tower_url=tower_url,
            environment=tower_environment,
            api_key=tower_api_key,
            inference_router=inference_router,
            inference_router_api_key=inference_router_api_key,
            inference_provider=inference_provider,
            jwt=tower_jwt,
        )
