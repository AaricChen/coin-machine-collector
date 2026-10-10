"""货道配货 / 库存 share 接口。"""

from __future__ import annotations

from typing import Optional

from hfyuwo.context import HfyuwoContext, create_context
from hfyuwo.models.base import RuoYiDataResult
from hfyuwo.models.track import FacilityTrackShare, TrackShareItem


def track_share_referer(facility_id: int) -> str:
    return f"https://ads.hfyuwo.com/facility_info/share/?disObj={facility_id}"


def get_facility_track_share(
    facility_id: int,
    *,
    ctx: Optional[HfyuwoContext] = None,
) -> FacilityTrackShare:
    """
    设备配货与货道库存，对应 GET /vending/track/share/{facilityId}。

    返回 data.list（各货道）与 data.facility（设备摘要）。
    """
    ctx = ctx or create_context()
    payload = ctx.client.get_json(
        f"vending/track/share/{facility_id}",
        referer=track_share_referer(facility_id),
    )
    result = RuoYiDataResult.from_payload(payload, FacilityTrackShare)
    return result.data


def list_track_share_items(
    facility_id: int,
    *,
    ctx: Optional[HfyuwoContext] = None,
) -> list[TrackShareItem]:
    """仅返回货道列表（常用快捷方法）。"""
    return get_facility_track_share(facility_id, ctx=ctx).tracks
