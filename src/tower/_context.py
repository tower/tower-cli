import os

class TowerContext:
    def __init__(self, tower_url: str, environment: str, api_key: str = None, hugging_face_provider: str = None, hugging_face_api_key: str = None):
        self.tower_url = tower_url
        self.environment = environment
        self.api_key = api_key
        self.hugging_face_provider = hugging_face_provider
        self.hugging_face_api_key = hugging_face_api_key

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
        hugging_face_provider = os.getenv("TOWER_HUGGING_FACE_PROVIDER")
        hugging_face_api_key = os.getenv("TOWER_HUGGING_FACE_API_KEY")

        return cls(
            tower_url = tower_url,
            environment = tower_environment,
            api_key = tower_api_key,
            hugging_face_provider = hugging_face_provider,
            hugging_face_api_key = hugging_face_api_key,
        )

