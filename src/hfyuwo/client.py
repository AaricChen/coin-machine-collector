"""hfyuwo 后台 HTTP 客户端（鉴权、重试）。"""

from __future__ import annotations

import time
from typing import Any, Mapping

import httpx
from loguru import logger

from config import Settings
from token_manager import TokenManager


class ApiError(Exception):
    def __init__(self, message: str, *, code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.code = code
        self.payload = payload


class HfyuwoClient:
    def __init__(self, settings: Settings, token_manager: TokenManager):
        self.settings = settings
        self.token_manager = token_manager

    def api_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.settings.api.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _auth_headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token_manager.get_valid_token()}",
            "isToken": "true",
            **self.settings.api.extra_headers,
        }
        if extra:
            headers.update(extra)
        return headers

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        referer: str | None = None,
    ) -> dict[str, Any]:
        url = self.api_url(path)
        extra_headers: dict[str, str] = {}
        if referer:
            extra_headers["Referer"] = referer
        return self._request_with_retry(method, url, extra_headers, params=params)

    def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        referer: str | None = None,
    ) -> dict[str, Any]:
        return self.request_json("GET", path, params=params, referer=referer)

    def _request_with_retry(
        self,
        method: str,
        url: str,
        extra_headers: dict[str, str],
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        max_attempts = 3
        token_refreshed = False

        for attempt in range(1, max_attempts + 1):
            headers = self._auth_headers(extra_headers)
            try:
                resp = httpx.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.settings.api.request_timeout,
                )
                if resp.status_code == 401:
                    if token_refreshed:
                        raise RuntimeError("Token 刷新后仍返回 401")
                    logger.warning("Token 失效，重新登录后重试")
                    self.token_manager.invalidate_token()
                    self.token_manager.login()
                    token_refreshed = True
                    continue
                resp.raise_for_status()
                payload = resp.json()
                if not isinstance(payload, dict):
                    return {"data": payload}
                return payload
            except httpx.HTTPError as e:
                if attempt == max_attempts:
                    raise
                wait_time = 2**attempt
                logger.warning(
                    "请求失败（第 {} 次）：{}，{} 秒后重试",
                    attempt,
                    e,
                    wait_time,
                )
                time.sleep(wait_time)

        raise RuntimeError("请求多次失败，无法获得有效响应")
