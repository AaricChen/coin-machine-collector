import json
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from config import Settings
from paths import resolve_from_root

TOKEN_CACHE_RELATIVE = "data/token_cache.json"


class TokenManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.token: Optional[str] = None
        self.expires_at: float = 0.0
        self._cache_file = resolve_from_root(TOKEN_CACHE_RELATIVE)

    def _load_from_cache(self) -> bool:
        if not self._cache_file.exists():
            return False
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            if data.get("token") and data.get("expires_at", 0) > time.time() + 60:
                self.token = data["token"]
                self.expires_at = data["expires_at"]
                logger.info(
                    "从缓存加载 Token，有效期至 {}",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.expires_at)),
                )
                return True
        except Exception as e:
            logger.warning("读取 Token 缓存失败：{}", e)
        return False

    def _save_to_cache(self, token: str, expires_in: int) -> None:
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "token": token,
            "expires_at": time.time() + expires_in,
            "created_at": time.time(),
        }
        self._cache_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            self._cache_file.chmod(0o600)
        except OSError:
            pass
        logger.info("Token 已缓存，有效期 {} 秒", expires_in)

    def _extract_token(self, response_data: dict[str, Any]) -> tuple[str, int]:
        token_path = self.settings.api.token_field
        value: Any = response_data
        for key in token_path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                break
        if not value:
            raise ValueError(f"无法从响应中提取 Token：{response_data}")

        expires_in = 3600
        if isinstance(response_data, dict):
            expires_in = int(
                response_data.get("expires_in")
                or response_data.get("expires_in_seconds")
                or response_data.get("data", {}).get("expires_in")
                or 3600
            )
        return str(value), expires_in

    def login(self) -> str:
        api = self.settings.api
        url = f"{api.base_url.rstrip('/')}{api.login_path}"
        payload = {
            "username": self.settings.credentials.username,
            "password": self.settings.credentials.password,
        }
        headers = {"Content-Type": "application/json", **api.extra_headers}

        logger.info("正在登录后台获取 Token...")
        with httpx.Client(timeout=api.request_timeout, headers=headers) as client:
            if api.login_method.upper() == "POST":
                if api.login_data_type == "json":
                    resp = client.post(url, json=payload)
                else:
                    resp = client.post(url, data=payload)
            else:
                resp = client.get(url, params=payload)

            resp.raise_for_status()
            data = resp.json()

        token, expires_in = self._extract_token(data)
        self.token = token
        self.expires_at = time.time() + expires_in
        self._save_to_cache(token, expires_in)
        return token

    def get_valid_token(self) -> str:
        if self.token and self.expires_at > time.time() + 60:
            return self.token
        if self._load_from_cache():
            return self.token or self.login()
        return self.login()

    def invalidate_token(self) -> None:
        self.token = None
        self.expires_at = 0
        if self._cache_file.exists():
            self._cache_file.unlink()
        logger.info("Token 缓存已清除")
