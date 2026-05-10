"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Agent Platform"
    debug: bool = False

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout: int = 120

    # Browser
    browser_headless: bool = True
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 720
    browser_timeout: int = 30000
    screenshot_dir: str = "/tmp/agent-screenshots"

    # VNC / Desktop
    vnc_host: str = "desktop"
    vnc_port: int = 5900
    novnc_port: int = 6080
    desktop_resolution: str = "1920x1080"

    # Vault
    vault_db_path: str = "/data/vault.db"
    vault_key_path: str = "/data/vault.key"

    # Streaming
    stream_fps: int = 10
    stream_quality: int = 60

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "AGENT_", "env_file": ".env"}


settings = Settings()
