"""运维同步报告数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from hfyuwo.models.facility import Facility
from hfyuwo.models.track import TrackShareItem


@dataclass
class FacilityExpiryStatus:
    facility_id: Optional[int]
    facility_number: Optional[str]
    facility_name: Optional[str]
    expiration_time: Optional[str]
    days_left: Optional[int]
    highlight: bool = False
    parse_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "facilityId": self.facility_id,
            "facilityNumber": self.facility_number,
            "facilityName": self.facility_name,
            "expirationTime": self.expiration_time,
            "daysLeft": self.days_left,
            "highlight": self.highlight,
            "parseError": self.parse_error,
        }


@dataclass
class LowStockAlert:
    facility_id: Optional[int]
    facility_name: Optional[str]
    track_id: Optional[int]
    track_number: Optional[int]
    goods_name: Optional[str]
    stock: int
    capacity: Optional[int]
    ratio: Optional[float]
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "facilityId": self.facility_id,
            "facilityName": self.facility_name,
            "trackId": self.track_id,
            "trackNumber": self.track_number,
            "goodsName": self.goods_name,
            "stock": self.stock,
            "capacity": self.capacity,
            "ratio": self.ratio,
            "reasons": self.reasons,
        }


@dataclass
class TrackInventoryLine:
    track: TrackShareItem
    low_stock: bool = False
    low_stock_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trackId": self.track.track_id,
            "trackNumber": self.track.track_number,
            "goodsName": self.track.goods_name,
            "trackExistingCount": self.track.track_existing_count,
            "trackCount": self.track.track_count,
            "trackGoodsPrice": self.track.track_goods_price,
            "lowStock": self.low_stock,
            "lowStockReasons": self.low_stock_reasons,
        }


@dataclass
class FacilityInventorySnapshot:
    facility: Facility
    tracks: list[TrackInventoryLine] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "facilityId": self.facility.facility_id,
            "facilityNumber": self.facility.facility_number,
            "facilityName": self.facility.facility_name,
            "error": self.error,
            "tracks": [t.to_dict() for t in self.tracks],
        }


@dataclass
class OpsSyncReport:
    fetched_at: str
    order_sync: dict[str, Any] = field(default_factory=dict)
    facilities: list[FacilityExpiryStatus] = field(default_factory=list)
    inventories: list[FacilityInventorySnapshot] = field(default_factory=list)
    expiry_highlights: list[FacilityExpiryStatus] = field(default_factory=list)
    low_stock_alerts: list[LowStockAlert] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fetchedAt": self.fetched_at,
            "orderSync": self.order_sync,
            "facilities": [f.to_dict() for f in self.facilities],
            "inventories": [i.to_dict() for i in self.inventories],
            "expiryHighlights": [f.to_dict() for f in self.expiry_highlights],
            "lowStockAlerts": [a.to_dict() for a in self.low_stock_alerts],
            "summary": {
                "facilityCount": len(self.facilities),
                "expiryHighlightCount": len(self.expiry_highlights),
                "lowStockAlertCount": len(self.low_stock_alerts),
                "orderCount": self.order_sync.get("orders_count"),
            },
        }
