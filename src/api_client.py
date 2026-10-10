import time
from typing import Any

from loguru import logger

from config import Settings
from hfyuwo.client import HfyuwoClient
from hfyuwo.context import HfyuwoContext
from hfyuwo.services.facility import list_all_facilities, list_facilities_page
from hfyuwo.services.track import list_track_share_items
from hfyuwo.services.user import get_user_info as fetch_user_info
from token_manager import TokenManager


class TokenExpiredError(Exception):
    pass


def _page_to_dict(page) -> dict[str, Any]:
    return {
        "code": page.code,
        "msg": page.msg,
        "total": page.total,
        "rows": [row.model_dump(by_alias=True) for row in page.rows],
    }


class ApiClient:
    """采集任务用门面；新业务优先使用 hfyuwo.services.* 独立函数。"""

    def __init__(self, settings: Settings, token_manager: TokenManager):
        self.settings = settings
        self.token_manager = token_manager
        self._ctx = HfyuwoContext(
            settings=settings,
            token_manager=token_manager,
            client=HfyuwoClient(settings, token_manager),
        )

    def get_user_info(self) -> dict[str, Any]:
        info = fetch_user_info(ctx=self._ctx)
        return info.model_dump(by_alias=True)

    def get_facility_list(
        self,
        page_num: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        page = list_facilities_page(page_num, page_size, ctx=self._ctx)
        logger.info(
            "获取设备列表成功，本页 {} 条，总计 {} 台",
            len(page.rows),
            page.total,
        )
        return _page_to_dict(page)

    def get_machine_list(self) -> list[dict]:
        facilities = list_all_facilities(ctx=self._ctx)
        rows = [f.model_dump(by_alias=True) for f in facilities]
        logger.info("获取机器列表成功，共 {} 台", len(rows))
        return rows

    def get_track_stock(self, machine_id: str) -> list[dict]:
        tracks = list_track_share_items(int(machine_id), ctx=self._ctx)
        track_list = [t.model_dump(by_alias=True) for t in tracks]
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
                        "track_name": track.get("goodsName")
                        or track.get("name")
                        or track.get("trackName"),
                        "stock": track.get("trackExistingCount")
                        or track.get("stock")
                        or track.get("count")
                        or 0,
                        "capacity": track.get("trackCount") or track.get("capacity"),
                        "collection_time": collection_time,
                    }
                )

        logger.info("采集完成，共生成 {} 条轨道库存记录", len(all_records))
        return all_records
