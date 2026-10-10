"""商品订单模型。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from hfyuwo.models.base import RuoYiModel


class GoodsOrder(RuoYiModel):
    shop_order_id: Optional[int] = Field(None, alias="shopOrderId")
    order_sn: Optional[str] = Field(None, alias="orderSn")
    hf_seq_id: Optional[str] = Field(None, alias="hfSeqId")
    pay_order_id: Optional[str] = Field(None, alias="payOrderId")
    create_time: Optional[str] = Field(None, alias="createTime")
    update_time: Optional[str] = Field(None, alias="updateTime")
    pay_time: Optional[str] = Field(None, alias="payTime")
    out_time: Optional[str] = Field(None, alias="outTime")
    refund_time: Optional[str] = Field(None, alias="refundTime")
    operator_id: Optional[int] = Field(None, alias="operatorId")
    operator_name: Optional[str] = Field(None, alias="operatorName")
    facility_id: Optional[int] = Field(None, alias="facilityId")
    facility_number: Optional[str] = Field(None, alias="facilityNumber")
    facility_name: Optional[str] = Field(None, alias="facilityName")
    track_id: Optional[int] = Field(None, alias="trackId")
    track_number: Optional[str] = Field(None, alias="trackNumber")
    goods_id: Optional[str] = Field(None, alias="goodsId")
    goods_name: Optional[str] = Field(None, alias="goodsName")
    goods_price: Optional[float] = Field(None, alias="goodsPrice")
    order_money: Optional[float] = Field(None, alias="orderMoney")
    discount_money: Optional[float] = Field(None, alias="discountMoney")
    refund_money: Optional[float] = Field(None, alias="refundMoney")
    pay_type: Optional[str] = Field(None, alias="payType")
    status: Optional[int] = None
    track_status: Optional[int] = Field(None, alias="trackStatus")
    order_type: Optional[int] = Field(None, alias="orderType")
    trans_status: Optional[int] = Field(None, alias="transStatus")
    delivery_code_status: Optional[int] = Field(None, alias="deliveryCodeStatus")
    out_num: Optional[int] = Field(None, alias="outNum")
    by_count: Optional[int] = Field(None, alias="byCount")

    @property
    def order_key(self) -> str:
        if self.shop_order_id is not None:
            return str(self.shop_order_id)
        return self.order_sn or ""


class GoodsOrderSummary(RuoYiModel):
    """listAll 返回的区间汇总（非订单明细）。"""

    all_money: Optional[float] = Field(None, alias="allMoney")
    all_count: Optional[int] = Field(None, alias="allCount")
    all_refund_money: Optional[float] = Field(None, alias="allRefundMoney")
    all_refund_count: Optional[int] = Field(None, alias="allRefundCount")
    all_wx_order_money: Optional[float] = Field(None, alias="allWxOrderMoney")
    all_wx_order_count: Optional[int] = Field(None, alias="allWxOrderCount")
    all_zfb_order_money: Optional[float] = Field(None, alias="allZfbOrderMoney")
    all_zfb_order_count: Optional[int] = Field(None, alias="allZfbOrderCount")
    all_other_order_money: Optional[float] = Field(None, alias="allOtherOrderMoney")
    all_other_order_count: Optional[int] = Field(None, alias="allOtherOrderCount")


@dataclass
class GoodsOrderTimeRange:
    """createTime 闭区间，格式 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS。"""

    begin_create_time: str
    end_create_time: str

    def to_query_params(self) -> dict[str, str]:
        return {
            "params[beginCreateTime]": self.begin_create_time,
            "params[endCreateTime]": self.end_create_time,
        }


@dataclass
class GoodsOrderSyncResult:
    mode: str
    orders: list[GoodsOrder]
    total_reported: int
    pages_fetched: int
    time_range: GoodsOrderTimeRange
    summary: Optional[GoodsOrderSummary] = None
    fetched_at: str = ""

    def __post_init__(self) -> None:
        if not self.fetched_at:
            self.fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def max_create_time(self) -> Optional[str]:
        times = [o.create_time for o in self.orders if o.create_time]
        return max(times) if times else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "fetched_at": self.fetched_at,
            "total_reported": self.total_reported,
            "pages_fetched": self.pages_fetched,
            "orders_count": len(self.orders),
            "time_range": {
                "beginCreateTime": self.time_range.begin_create_time,
                "endCreateTime": self.time_range.end_create_time,
            },
            "max_create_time": self.max_create_time,
            "summary": self.summary.model_dump(by_alias=True) if self.summary else None,
        }
