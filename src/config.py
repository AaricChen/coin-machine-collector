import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from paths import PROJECT_ROOT, resolve_from_root


class ApiConfig(BaseModel):
    base_url: str
    login_path: str
    machine_list_path: str
    track_stock_path: str
    login_method: str = "POST"
    login_data_type: str = "json"
    token_field: str = "data.token"
    extra_headers: dict[str, str] = Field(default_factory=dict)
    request_timeout: int = 30


class Credentials(BaseModel):
    username: str = ""
    password: str = ""
    keychain_service: str = ""
    keychain_username_key: str = ""


class StorageConfig(BaseModel):
    db_path: str = "data/coin_machine.db"


class ScheduleConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    cron: Optional[str] = None
    interval_minutes: Optional[int] = None


class AppConfig(BaseModel):
    run_mode: str = "once"
    interval_minutes: int = 60


class Settings(BaseSettings):
    app: AppConfig
    api: ApiConfig
    credentials: Credentials
    storage: StorageConfig
    schedule: ScheduleConfig

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=str(PROJECT_ROOT / ".env"),
        extra="ignore",
    )

    @property
    def db_path_resolved(self) -> Path:
        return resolve_from_root(self.storage.db_path)


def _maybe_keychain_password(credentials: dict[str, Any]) -> None:
    service = credentials.get("keychain_service") or ""
    if not service:
        return
    try:
        import keyring
    except ImportError:
        return
    user_key = credentials.get("keychain_username_key") or "username"
    pwd_key = credentials.get("keychain_password_key") or "password"
    if not credentials.get("username"):
        credentials["username"] = keyring.get_password(service, user_key) or ""
    if not credentials.get("password"):
        credentials["password"] = keyring.get_password(service, pwd_key) or ""


def load_config(config_path: Optional[str | Path] = None) -> Settings:
    path = Path(config_path) if config_path else PROJECT_ROOT / "config" / "settings.yaml"
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    with open(path, encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f) or {}

    creds = yaml_data.setdefault("credentials", {})
    creds["username"] = os.getenv("COIN_MACHINE_USERNAME", creds.get("username", ""))
    creds["password"] = os.getenv("COIN_MACHINE_PASSWORD", creds.get("password", ""))
    _maybe_keychain_password(creds)

    return Settings(**yaml_data)
