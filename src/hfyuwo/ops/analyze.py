"""到期 / 低库存纯函数分析。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from config import OpsConfig
from hfyuwo.models.facility import Facility
from hfyuwo.models.track import TrackShareItem
from hfyuwo.ops.models import FacilityExpiryStatus, LowStockAlert


def parse_expiration_time(value: Optional[str]) -> Optional[datetime]:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return None


def classify_facility_expiry(
    facility: Facility,
    warn_days: int,
    *,
    now: Optional[datetime] = None,
) -> FacilityExpiryStatus:
    now = now or datetime.now()
    exp = parse_expiration_time(facility.expiration_time)
    if exp is None:
        return FacilityExpiryStatus(
            facility_id=facility.facility_id,
            facility_number=facility.facility_number,
            facility_name=facility.facility_name,
            expiration_time=facility.expiration_time,
            days_left=None,
            highlight=False,
            parse_error=bool(facility.expiration_time),
        )
    days_left = (exp.date() - now.date()).days
    return FacilityExpiryStatus(
        facility_id=facility.facility_id,
        facility_number=facility.facility_number,
        facility_name=facility.facility_name,
        expiration_time=facility.expiration_time,
        days_left=days_left,
        highlight=days_left <= warn_days,
        parse_error=False,
    )


def is_low_stock(
    track: TrackShareItem,
    ops: OpsConfig,
) -> tuple[bool, list[str], Optional[float]]:
    """绝对阈值 OR 比例阈值，任一命中即低库存。容量为 0/null 时跳过比例。"""
    stock = track.stock
    capacity = track.capacity
    reasons: list[str] = []
    ratio: Optional[float] = None

    if capacity is not None and capacity > 0:
        ratio = stock / float(capacity)

    if ops.low_stock_absolute is not None and stock <= ops.low_stock_absolute:
        reasons.append(f"absolute<={ops.low_stock_absolute}")

    if (
        ops.low_stock_ratio is not None
        and ratio is not None
        and ratio <= ops.low_stock_ratio
    ):
        reasons.append(f"ratio<={ops.low_stock_ratio}")

    return bool(reasons), reasons, ratio


def build_low_stock_alert(
    facility: Facility,
    track: TrackShareItem,
    reasons: list[str],
    ratio: Optional[float],
) -> LowStockAlert:
    return LowStockAlert(
        facility_id=facility.facility_id,
        facility_name=facility.facility_name,
        track_id=track.track_id,
        track_number=track.track_number,
        goods_name=track.goods_name,
        stock=track.stock,
        capacity=track.capacity,
        ratio=ratio,
        reasons=reasons,
    )
