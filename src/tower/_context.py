import os

class TowerContext:
    def __init__(self, tower_url: str, environment: str, api_key: str = None, 
                 inference_router: str = None, inference_router_api_key: str = None,
                 inference_service: str = None):
        self.tower_url = tower_url
        self.environment = environment
        self.api_key = api_key
        self.inference_router = inference_router
        self.inference_router_api_key = inference_router_api_key
        self.inference_service = inference_service

    def is_local(self) -> bool:
        if self.environment is None or self.environment == "":
            return True
        elif self.environment == "local":
            return True
        else:
            return False

    @classmethod
    def build(cls):
        tower_url = os.getenv("TOWER_URL")
        tower_environment = os.getenv("TOWER_ENVIRONMENT")
        tower_api_key = os.getenv("TOWER_API_KEY")

        # Replaces the deprecated hugging_face_provider and hugging_face_api_key
        inference_router = os.getenv("TOWER_INFERENCE_ROUTER")
        inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
        inference_service = os.getenv("TOWER_INFERENCE_SERVICE")


        return cls(
            tower_url = tower_url,
            environment = tower_environment,
            api_key = tower_api_key,
            inference_router = inference_router,
            inference_router_api_key = inference_router_api_key,
            inference_service = inference_service,
        )

