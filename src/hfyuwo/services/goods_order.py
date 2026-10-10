"""商品订单：分页明细 list + 汇总 listAll + 全量/增量拉取。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from hfyuwo.context import HfyuwoContext, create_context
from hfyuwo.models.base import RuoYiDataResult, RuoYiPage, fetch_all_pages
from hfyuwo.models.goods_order import (
    GoodsOrder,
    GoodsOrderSummary,
    GoodsOrderSyncResult,
    GoodsOrderTimeRange,
)
from paths import PROJECT_ROOT

GOODS_ORDER_LIST_PATH = "vending/goods_order/list"
GOODS_ORDER_LIST_ALL_PATH = "vending/goods_order/listAll"
GOODS_ORDER_REFERER = "https://ads.hfyuwo.com/goods_order/goodsOrder"

DEFAULT_SYNC_STATE_PATH = PROJECT_ROOT / "data" / "goods_order_sync_state.json"


def _list_params(
    time_range: GoodsOrderTimeRange,
    page_num: int,
    page_size: int,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "pageNum": page_num,
        "pageSize": page_size,
        **time_range.to_query_params(),
    }
    if extra:
        params.update(extra)
    return params


def list_goods_orders_page(
    time_range: GoodsOrderTimeRange,
    page_num: int = 1,
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
    extra_params: Optional[dict[str, Any]] = None,
) -> RuoYiPage[GoodsOrder]:
    """分页订单明细 → GET /vending/goods_order/list。"""
    ctx = ctx or create_context()
    payload = ctx.client.get_json(
        GOODS_ORDER_LIST_PATH,
        params=_list_params(time_range, page_num, page_size, extra_params),
        referer=GOODS_ORDER_REFERER,
    )
    return RuoYiPage.from_payload(payload, GoodsOrder)


def get_goods_order_summary(
    time_range: GoodsOrderTimeRange,
    *,
    ctx: Optional[HfyuwoContext] = None,
    extra_params: Optional[dict[str, Any]] = None,
) -> GoodsOrderSummary:
    """区间汇总 → GET /vending/goods_order/listAll（金额/笔数统计，非订单列表）。"""
    ctx = ctx or create_context()
    payload = ctx.client.get_json(
        GOODS_ORDER_LIST_ALL_PATH,
        params={
            "pageNum": 1,
            "pageSize": 50,
            **time_range.to_query_params(),
            **(extra_params or {}),
        },
        referer=GOODS_ORDER_REFERER,
    )
    result = RuoYiDataResult.from_payload(payload, GoodsOrderSummary)
    return result.data


def fetch_all_goods_orders(
    time_range: GoodsOrderTimeRange,
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
    extra_params: Optional[dict[str, Any]] = None,
) -> tuple[list[GoodsOrder], int, int]:
    """指定 createTime 区间内拉取全部订单明细页。"""
    ctx = ctx or create_context()
    first = list_goods_orders_page(
        time_range, 1, page_size, ctx=ctx, extra_params=extra_params
    )
    pages_fetched = 1

    def _fetch(page_num: int, size: int) -> RuoYiPage[GoodsOrder]:
        nonlocal pages_fetched
        pages_fetched = max(pages_fetched, page_num)
        return list_goods_orders_page(
            time_range, page_num, size, ctx=ctx, extra_params=extra_params
        )

    orders = fetch_all_pages(_fetch, page_size=page_size)
    if pages_fetched == 1 and len(orders) > len(first.rows):
        pages_fetched = (len(orders) + page_size - 1) // page_size
    return orders, first.total, pages_fetched


def sync_goods_orders_full(
    time_range: GoodsOrderTimeRange,
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
    include_summary: bool = True,
) -> GoodsOrderSyncResult:
    """
    全量同步：按 createTime 区间分页拉完 list，并可选拉 listAll 汇总校验。
    """
    ctx = ctx or create_context()
    orders, total, pages = fetch_all_goods_orders(
        time_range, page_size=page_size, ctx=ctx
    )
    summary = (
        get_goods_order_summary(time_range, ctx=ctx) if include_summary else None
    )
    logger.info(
        "订单全量同步 {} ~ {}：{} 条（接口 total={}，{} 页）",
        time_range.begin_create_time,
        time_range.end_create_time,
        len(orders),
        total,
        pages,
    )
    return GoodsOrderSyncResult(
        mode="full",
        orders=orders,
        total_reported=total,
        pages_fetched=pages,
        time_range=time_range,
        summary=summary,
    )


def load_sync_state(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_SYNC_STATE_PATH
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("读取订单同步状态失败：{}", e)
        return {}


def save_sync_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or DEFAULT_SYNC_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _default_incremental_begin(
    state: dict[str, Any],
    overlap_minutes: int,
) -> str:
    cursor = state.get("last_create_time") or state.get("last_end_create_time")
    if cursor:
        try:
            dt = datetime.strptime(cursor, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.strptime(cursor[:10], "%Y-%m-%d")
        begin = dt - timedelta(minutes=overlap_minutes)
        return begin.strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d")


def sync_goods_orders_incremental(
    *,
    end_create_time: str | None = None,
    overlap_minutes: int = 10,
    page_size: int = 50,
    ctx: Optional[HfyuwoContext] = None,
    state_path: Path | None = None,
    include_summary: bool = False,
    persist_state: bool = True,
) -> GoodsOrderSyncResult:
    """
    增量同步：从状态文件中的 last_create_time 往前 overlap 起，拉到 end_create_time（默认当前时刻）。

    状态文件默认 data/goods_order_sync_state.json。
    """
    ctx = ctx or create_context()
    state = load_sync_state(state_path)
    end = end_create_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    begin = _default_incremental_begin(state, overlap_minutes)
    time_range = GoodsOrderTimeRange(begin_create_time=begin, end_create_time=end)

    orders, total, pages = fetch_all_goods_orders(
        time_range, page_size=page_size, ctx=ctx
    )
    summary = (
        get_goods_order_summary(time_range, ctx=ctx) if include_summary else None
    )

    result = GoodsOrderSyncResult(
        mode="incremental",
        orders=orders,
        total_reported=total,
        pages_fetched=pages,
        time_range=time_range,
        summary=summary,
    )

    if persist_state:
        new_state = {
            **state,
            "last_sync_at": result.fetched_at,
            "last_end_create_time": end,
            "last_create_time": result.max_create_time or state.get("last_create_time"),
            "last_mode": "incremental",
            "last_orders_count": len(orders),
        }
        save_sync_state(new_state, state_path)

    logger.info(
        "订单增量同步 {} ~ {}：{} 条",
        begin,
        end,
        len(orders),
    )
    return result


def sync_goods_orders_full_and_save_state(
    time_range: GoodsOrderTimeRange,
    page_size: int = 50,
    *,
    ctx: Optional[HfyuwoContext] = None,
    state_path: Path | None = None,
) -> GoodsOrderSyncResult:
    """全量同步并写入增量游标（便于后续 incremental）。"""
    result = sync_goods_orders_full(
        time_range, page_size=page_size, ctx=ctx, include_summary=True
    )
    save_sync_state(
        {
            "last_sync_at": result.fetched_at,
            "last_end_create_time": time_range.end_create_time,
            "last_create_time": result.max_create_time,
            "last_mode": "full",
            "last_orders_count": len(result.orders),
            "full_range": time_range.to_query_params(),
        },
        state_path,
    )
    return result
