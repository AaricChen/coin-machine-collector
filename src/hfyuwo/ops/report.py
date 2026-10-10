"""运维报告渲染与日志输出。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from paths import PROJECT_ROOT
from hfyuwo.ops.models import OpsSyncReport


def render_ops_report(report: OpsSyncReport) -> str:
    lines: list[str] = []
    lines.append(f"=== 运维同步报告 {report.fetched_at} ===")

    order = report.order_sync
    lines.append("")
    lines.append("[订单增量]")
    lines.append(
        f"  条数={order.get('orders_count')} total_reported={order.get('total_reported')} "
        f"窗口={order.get('time_range')} max_create_time={order.get('max_create_time')}"
    )

    lines.append("")
    lines.append(f"[设备到期] 共 {len(report.facilities)} 台")
    for f in report.facilities:
        tag = " [HIGHLIGHT]" if f.highlight else ""
        days = "unknown" if f.days_left is None else str(f.days_left)
        lines.append(
            f"  {f.facility_id} {f.facility_name} "
            f"到期={f.expiration_time} 剩余天={days}{tag}"
        )

    lines.append("")
    lines.append(f"[货道库存] 共 {len(report.inventories)} 台设备")
    for inv in report.inventories:
        name = inv.facility.facility_name
        if inv.error:
            lines.append(f"  {inv.facility.facility_id} {name} ERROR: {inv.error}")
            continue
        lines.append(f"  --- {inv.facility.facility_id} {name} ({len(inv.tracks)} 货道) ---")
        for line in inv.tracks:
            t = line.track
            tag = " [HIGHLIGHT]" if line.low_stock else ""
            lines.append(
                f"    道{t.track_number} {t.goods_name} "
                f"库存={t.stock}/{t.capacity} 价={t.track_goods_price}{tag}"
            )

    lines.append("")
    lines.append(
        f"[汇总] 临期 highlight={len(report.expiry_highlights)} "
        f"低库存 highlight={len(report.low_stock_alerts)}"
    )
    return "\n".join(lines)


def log_ops_report(report: OpsSyncReport) -> None:
    logger.info("\n{}", render_ops_report(report))
    for f in report.expiry_highlights:
        logger.warning(
            "[HIGHLIGHT] 设备临期：{} {} 到期={} 剩余天={}",
            f.facility_id,
            f.facility_name,
            f.expiration_time,
            f.days_left,
        )
    for a in report.low_stock_alerts:
        logger.warning(
            "[HIGHLIGHT] 库存不足：设备={} {} 道{} {} 库存={}/{} reasons={}",
            a.facility_id,
            a.facility_name,
            a.track_number,
            a.goods_name,
            a.stock,
            a.capacity,
            a.reasons,
        )


def maybe_write_report_json(report: OpsSyncReport, enabled: bool) -> Path | None:
    if not enabled:
        return None
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir / f"ops_sync_{stamp}.json"
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("运维报告 JSON 已写入 {}", path)
    return path
