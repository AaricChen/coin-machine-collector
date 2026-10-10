import time
from typing import Any

import httpx
from loguru import logger

from config import Settings
from token_manager import TokenManager


class TokenExpiredError(Exception):
    pass


class ApiClient:
    def __init__(self, settings: Settings, token_manager: TokenManager):
        self.settings = settings
        self.token_manager = token_manager

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token_manager.get_valid_token()}",
            "isToken": "true",
            **self.settings.api.extra_headers,
        }

    @staticmethod
    def _unwrap_list(data: Any, *keys: str) -> list[dict]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if not isinstance(data, dict):
            return []
        inner = data.get("data", data)
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            for key in ("rows", *keys):
                candidate = inner.get(key)
                if isinstance(candidate, list):
                    return candidate
        return []

    def _request_with_retry(self, method: str, url: str) -> dict[str, Any]:
        max_attempts = 3
        token_refreshed = False

        for attempt in range(1, max_attempts + 1):
            headers = self._get_headers()
            try:
                resp = httpx.request(
                    method,
                    url,
                    headers=headers,
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
            except TokenExpiredError:
                self.token_manager.invalidate_token()
                self.token_manager.login()
                token_refreshed = True
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

    def get_user_info(self) -> dict[str, Any]:
        url = (
            f"{self.settings.api.base_url.rstrip('/')}"
            f"{self.settings.api.user_info_path}"
        )
        data = self._request_with_retry("GET", url)
        if isinstance(data.get("user"), dict):
            return data
        return data

    def get_machine_list(self) -> list[dict]:
        path = self.settings.api.machine_list_path
        if "pageNum=" not in path:
            sep = "&" if "?" in path else "?"
            path = f"{path}{sep}pageNum=1&pageSize=500"
        url = f"{self.settings.api.base_url.rstrip('/')}{path}"
        data = self._request_with_retry("GET", url)
        machine_list = self._unwrap_list(data, "machines", "list", "records")
        logger.info("获取机器列表成功，共 {} 台", len(machine_list))
        return machine_list

    def get_track_stock(self, machine_id: str) -> list[dict]:
        path = self.settings.api.track_stock_path.format(machine_id=machine_id)
        url = f"{self.settings.api.base_url.rstrip('/')}{path}"
        data = self._request_with_retry("GET", url)
        track_list = self._unwrap_list(data, "tracks", "list", "records")
        logger.debug(
            "机器 {} 轨道库存获取成功，共 {} 条",
            machine_id,
            len(track_list),
        )
        return track_list

    def collect_all(self) -> list[dict]:
        machines = self.get_machine_list()
        all_records: list[dict] = []
        collection_time = time.strftime("%Y-%m-%d %H:%M:%S")

        for machine in machines:
            machine_id = (
                machine.get("id")
                or machine.get("machineId")
                or machine.get("deviceId")
                or machine.get("facilityId")
                or machine.get("facilityNumber")
            )
            if not machine_id:
                logger.warning("跳过缺少 ID 的机器记录：{}", machine)
                continue

            tracks = self.get_track_stock(str(machine_id))
            for track in tracks:
                all_records.append(
                    {
                        "machine_id": str(machine_id),
                        "machine_name": machine.get("name")
                        or machine.get("deviceName")
                        or machine.get("facilityName"),
                        "track_id": track.get("trackId") or track.get("id"),
                        "track_name": track.get("name") or track.get("trackName"),
                        "stock": track.get("stock") or track.get("count") or 0,
                        "capacity": track.get("capacity"),
                        "collection_time": collection_time,
                    }
                )

        logger.info("采集完成，共生成 {} 条轨道库存记录", len(all_records))
        return all_records
