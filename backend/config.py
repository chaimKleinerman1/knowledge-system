from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# LiteLLM reads GEMINI_API_KEY from os.environ, so the .env file must reach the
# process environment and not only the settings object.
load_dotenv()

DEFAULT_MONGODB_URI = "mongodb://localhost:27017"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MONGODB_URI: str = DEFAULT_MONGODB_URI
    MONGODB_DB_NAME: str = "knowledge"
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini/gemini-3.1-flash-lite"
    EMBEDDING_MODEL: str = "gemini/gemini-embedding-2"
    EMBEDDING_DIMENSIONS: int = 768
    MAX_IMAGE_BYTES: int = 10 * 1024 * 1024
    MAX_TEXT_BYTES: int = 1024 * 1024
    MAX_IMAGE_PIXELS_SIDE: int = 8000
    LLM_TEXT_INPUT_CHARS: int = 20000
    LLM_MAX_OUTPUT_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 3
    AI_CONCURRENCY: int = 2
    # Measured with gemini-embedding-2 on the sample set: true matches score 0.50-0.59, while
    # nonsense queries reach 0.47 against a number-heavy receipt, so 0.5 keeps the noise out.
    SEMANTIC_MIN_SCORE: float = 0.5
    SEARCH_LIMIT: int = 10
    CORS_ORIGINS: str = "http://localhost:5173"
    PORT: int = 8000

    @field_validator("MONGODB_URI", mode="before")
    @classmethod
    def blank_uri_means_default(cls, value: object) -> object:
        # The shared .env may leave MONGODB_URI empty to mean "use the local database".
        if isinstance(value, str) and not value.strip():
            return DEFAULT_MONGODB_URI
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
