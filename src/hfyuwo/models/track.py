"""货道 / 配货（track share）模型。"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from hfyuwo.models.base import RuoYiModel
from hfyuwo.models.facility import FacilityDetail


class TrackShareItem(RuoYiModel):
    """单货道配货与库存信息。"""

    track_id: Optional[int] = Field(None, alias="trackId")
    facility_id: Optional[int] = Field(None, alias="facilityId")
    track_number: Optional[int] = Field(None, alias="trackNumber")
    track_count: Optional[int] = Field(None, alias="trackCount")
    track_existing_count: Optional[int] = Field(None, alias="trackExistingCount")
    track_status: Optional[str] = Field(None, alias="trackStatus")
    track_start_status: Optional[str] = Field(None, alias="trackStartStatus")
    track_discount: Optional[float] = Field(None, alias="trackDiscount")
    track_discount_price: Optional[float] = Field(None, alias="trackDiscountPrice")
    track_goods_price: Optional[float] = Field(None, alias="trackGoodsPrice")
    discount_price: Optional[float] = Field(None, alias="disCountPrice")
    alarm_code: Optional[int] = Field(None, alias="alarmCode")
    test_status: Optional[int] = Field(None, alias="testStatus")
    discount_status: Optional[int] = Field(None, alias="discountStatus")
    goods_id: Optional[int] = Field(None, alias="goodsId")
    goods_name: Optional[str] = Field(None, alias="goodsName")
    goods_img: Optional[str] = Field(None, alias="goodsImg")
    product_number: Optional[str] = Field(None, alias="productNumber")
    product_start_date: Optional[str] = Field(None, alias="productStartDate")
    product_end_date: Optional[str] = Field(None, alias="productEndDate")

    @property
    def stock(self) -> int:
        return int(self.track_existing_count or 0)

    @property
    def capacity(self) -> int | None:
        return self.track_count

    @property
    def track_name(self) -> str | None:
        if self.goods_name:
            return self.goods_name
        if self.track_number is not None:
            return f"货道{self.track_number}"
        return None


class FacilityTrackShare(RuoYiModel):
    """GET /vending/track/share/{facilityId} 的 data 段。"""

    facility: Optional[FacilityDetail] = None
    tracks: list[TrackShareItem] = Field(default_factory=list, alias="list")
