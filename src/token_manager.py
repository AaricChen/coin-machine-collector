import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from captcha import CaptchaClient
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
        if response_data.get("code") not in (None, 200):
            raise ValueError(
                f"登录失败：{response_data.get('msg') or response_data}"
            )

        token_path = self.settings.api.token_field
        value: Any = response_data
        for key in token_path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                break
        if not value:
            raise ValueError(f"无法从响应中提取 Token：{response_data}")

        expires_in = self.settings.api.token_ttl_seconds
        if isinstance(response_data, dict):
            expires_in = int(
                response_data.get("expires_in")
                or response_data.get("expires_in_seconds")
                or response_data.get("data", {}).get("expires_in")
                or expires_in
            )
        return str(value), expires_in

    def login(self) -> str:
        api = self.settings.api
        url = f"{api.base_url.rstrip('/')}{api.login_path}"
        manual_captcha = os.getenv("COIN_MACHINE_CAPTCHA_CODE", "").strip() or None
        captcha_client = CaptchaClient(self.settings)
        base_headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "isToken": "false",
            **api.extra_headers,
        }

        logger.info("正在登录后台获取 Token...")
        last_error: Optional[str] = None
        with httpx.Client(timeout=api.request_timeout) as client:
            for attempt in range(1, api.login_max_attempts + 1):
                payload: dict[str, Any] = {
                    "username": self.settings.credentials.username,
                    "password": self.settings.credentials.password,
                }
                if api.captcha_enabled:
                    uuid, img_bytes = captcha_client.fetch(client)
                    code = captcha_client.solve(
                        img_bytes,
                        manual_code=manual_captcha if attempt == 1 else None,
                    )
                    payload["uuid"] = uuid
                    payload["code"] = code
                    logger.debug("登录尝试 {}/{}，验证码={}", attempt, api.login_max_attempts, code)

                if api.login_method.upper() == "POST":
                    if api.login_data_type == "json":
                        resp = client.post(url, json=payload, headers=base_headers)
                    else:
                        resp = client.post(url, data=payload, headers=base_headers)
                else:
                    resp = client.get(url, params=payload, headers=base_headers)

                resp.raise_for_status()
                data = resp.json()
                if data.get("code") == 200:
                    token, expires_in = self._extract_token(data)
                    self.token = token
                    self.expires_at = time.time() + expires_in
                    self._save_to_cache(token, expires_in)
                    return token

                last_error = str(data.get("msg") or data)
                logger.warning(
                    "登录失败（{}/{}）：{}",
                    attempt,
                    api.login_max_attempts,
                    last_error,
                )
                if manual_captcha and attempt == 1:
                    manual_captcha = None

        raise RuntimeError(f"登录多次失败：{last_error}")

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
