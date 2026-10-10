"""设备与货道数据采集（复用 services）。"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from config import OpsConfig
from hfyuwo.context import HfyuwoContext
from hfyuwo.models.facility import Facility
from hfyuwo.ops.analyze import build_low_stock_alert, is_low_stock
from hfyuwo.ops.models import FacilityInventorySnapshot, LowStockAlert, TrackInventoryLine
from hfyuwo.services.facility import list_all_facilities
from hfyuwo.services.track import get_facility_track_share


def collect_facilities(
    ctx: HfyuwoContext,
    *,
    page_size: int = 50,
) -> list[Facility]:
    return list_all_facilities(page_size=page_size, ctx=ctx)


def collect_all_track_shares(
    ctx: HfyuwoContext,
    facilities: list[Facility],
    ops: OpsConfig,
) -> tuple[list[FacilityInventorySnapshot], list[LowStockAlert]]:
    """按设备拉取货道配货；单台失败记 warning 不中断。"""
    snapshots: list[FacilityInventorySnapshot] = []
    alerts: list[LowStockAlert] = []

    for facility in facilities:
        fid = facility.facility_id
        if fid is None:
            logger.warning("跳过缺少 facilityId 的设备：{}", facility.facility_name)
            continue
        try:
            share = get_facility_track_share(fid, ctx=ctx)
            lines: list[TrackInventoryLine] = []
            for track in share.tracks:
                low, reasons, ratio = is_low_stock(track, ops)
                lines.append(
                    TrackInventoryLine(
                        track=track,
                        low_stock=low,
                        low_stock_reasons=reasons,
                    )
                )
                if low:
                    alerts.append(
                        build_low_stock_alert(facility, track, reasons, ratio)
                    )
            snapshots.append(
                FacilityInventorySnapshot(facility=facility, tracks=lines)
            )
        except Exception as e:
            logger.warning(
                "拉取设备 {} ({}) 货道失败：{}",
                fid,
                facility.facility_name,
                e,
            )
            snapshots.append(
                FacilityInventorySnapshot(facility=facility, tracks=[], error=str(e))
            )

    return snapshots, alerts
