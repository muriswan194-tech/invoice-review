from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    """Fixed Northstar policy and local storage configuration. Not environment-driven."""

    customer_vat_id: str = "NL00449544B01"
    total_tolerance: Decimal = Decimal("0.01")
    low_confidence_threshold: float = 0.80
    max_upload_bytes: int = 4 * 1024 * 1024
    data_dir: Path = BACKEND_DIR / "data"
    upload_dir: Path = BACKEND_DIR / "data" / "uploads"
    static_dir: Path = BACKEND_DIR / "static"
    database_url: str = f"sqlite:///{BACKEND_DIR / 'data' / 'invoice-review.db'}"
    # localhost and 127.0.0.1 are distinct browser origins, so both are listed.
    allowed_origins: tuple[str, ...] = (
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


APP_CONFIG = AppConfig()


class Settings(BaseSettings):
    document_intelligence_endpoint: str = Field(
        validation_alias="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
    )
    document_intelligence_key: str = Field(validation_alias="AZURE_DOCUMENT_INTELLIGENCE_KEY")
    openai_endpoint: str = Field(validation_alias="AZURE_OPENAI_ENDPOINT")
    openai_deployment: str = Field(validation_alias="AZURE_OPENAI_DEPLOYMENT")
    openai_api_key: str = Field(validation_alias="AZURE_OPENAI_API_KEY")
    foundry_project_endpoint: str = Field(validation_alias="FOUNDRY_PROJECT_ENDPOINT")
    foundry_agent_name: str = Field(validation_alias="FOUNDRY_AGENT_NAME")
    foundry_agent_version: str = Field(validation_alias="FOUNDRY_AGENT_VERSION")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


settings = Settings()
