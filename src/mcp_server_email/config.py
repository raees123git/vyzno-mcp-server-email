from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8000, ge=1, le=65535)

    vyzno_base_url: HttpUrl
    vyzno_origin: str = "https://vyzno.io"

    vyzno_cookie_header: SecretStr = Field(min_length=1)
    vyzno_csrf_token: SecretStr = Field(min_length=1)