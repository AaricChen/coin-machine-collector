"""运维同步入口：独立可调用，供定时任务复用。"""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from config import Settings
from hfyuwo.context import create_context
from hfyuwo.ops.analyze import classify_facility_expiry
from hfyuwo.ops.collect import collect_all_track_shares, collect_facilities
from hfyuwo.ops.models import OpsSyncReport
from hfyuwo.ops.report import log_ops_report, maybe_write_report_json
from hfyuwo.services.goods_order import sync_goods_orders_incremental


def run_scheduled_ops_sync(settings: Settings) -> OpsSyncReport:
    """
    一次运维同步：订单增量 + 全量设备到期分析 + 全量货道库存/低库存 highlight。

    示例::
        from config import load_config
        from hfyuwo.ops.sync import run_scheduled_ops_sync
        report = run_scheduled_ops_sync(load_config())
    """
    ops = settings.ops
    ctx = create_context()
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info("开始运维同步作业…")

    order_result = sync_goods_orders_incremental(
        overlap_minutes=ops.order_sync_overlap_minutes,
        page_size=ops.order_sync_page_size,
        ctx=ctx,
        include_summary=False,
        persist_state=True,
    )
    order_sync = order_result.to_dict()

    facilities = collect_facilities(ctx)
    expiry_statuses = [
        classify_facility_expiry(f, ops.facility_expiry_warn_days)
        for f in facilities
    ]
    expiry_highlights = [s for s in expiry_statuses if s.highlight]

    inventories, low_stock_alerts = collect_all_track_shares(ctx, facilities, ops)

    report = OpsSyncReport(
        fetched_at=fetched_at,
        order_sync=order_sync,
        facilities=expiry_statuses,
        inventories=inventories,
        expiry_highlights=expiry_highlights,
        low_stock_alerts=low_stock_alerts,
    )

    log_ops_report(report)
    maybe_write_report_json(report, ops.write_report_json)
    logger.success(
        "运维同步完成：订单 {} 条，设备 {} 台，临期 {}，低库存 {}",
        order_sync.get("orders_count"),
        len(facilities),
        len(expiry_highlights),
        len(low_stock_alerts),
    )
    return report
