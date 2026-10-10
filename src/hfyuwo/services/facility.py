"""设备列表业务接口（可独立 import 调用）。"""

from __future__ import annotations

from typing import Optional

from hfyuwo.context import HfyuwoContext, create_context
from hfyuwo.models.base import RuoYiDataResult, RuoYiPage, fetch_all_pages
from hfyuwo.models.facility import Facility, FacilityDetail

FACILITY_LIST_REFERER = "https://ads.hfyuwo.com/equipment/facility"


def facility_detail_referer(facility_id: int, facility_number: str | None = None) -> str:
    number = facility_number or ""
    return (
        "https://ads.hfyuwo.com/facility/facility_info/"
        f"?disObj={facility_id}&facilityNumber={number}"
    )


def list_facilities_page(
    page_num: int = 1,
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
) -> RuoYiPage[Facility]:
    """
    单页设备列表，对应 GET /vending/facility/list。

    示例:
        from hfyuwo.services.facility import list_facilities_page
        page = list_facilities_page(1, 50)
        for f in page.rows:
            print(f.facility_name)
    """
    ctx = ctx or create_context()
    base_path = ctx.settings.api.machine_list_path.split("?", 1)[0].lstrip("/")
    payload = ctx.client.get_json(
        base_path,
        params={"pageNum": page_num, "pageSize": page_size},
        referer=FACILITY_LIST_REFERER,
    )
    page = RuoYiPage.from_payload(payload, Facility)
    return page


def list_all_facilities(
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
) -> list[Facility]:
    """按 total 自动翻页，返回全部设备。"""
    ctx = ctx or create_context()

    def _fetch(page_num: int, size: int) -> RuoYiPage[Facility]:
        return list_facilities_page(page_num, size, ctx=ctx)

    return fetch_all_pages(_fetch, page_size=page_size)


def get_facility_detail(
    facility_id: int,
    *,
    facility_number: str | None = None,
    ctx: Optional[HfyuwoContext] = None,
) -> FacilityDetail:
    """
    设备详情，对应 GET /vending/facility/{facilityId}。

    facility_number 仅用于 Referer，与浏览器一致；不传也可请求。
    """
    ctx = ctx or create_context()
    payload = ctx.client.get_json(
        f"vending/facility/{facility_id}",
        referer=facility_detail_referer(facility_id, facility_number),
    )
    result = RuoYiDataResult.from_payload(payload, FacilityDetail)
    return result.data
