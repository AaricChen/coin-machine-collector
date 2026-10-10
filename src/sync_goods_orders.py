"""CLI：商品订单全量 / 增量同步。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hfyuwo.models.goods_order import GoodsOrderTimeRange  # noqa: E402
from hfyuwo.services.goods_order import (  # noqa: E402
    get_goods_order_summary,
    list_goods_orders_page,
    sync_goods_orders_full,
    sync_goods_orders_incremental,
    sync_goods_orders_full_and_save_state,
)
from logger import setup_logger  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="商品订单同步（list + listAll 汇总）")
    sub = parser.add_subparsers(dest="command", required=True)

    p_page = sub.add_parser("page", help="拉取单页明细")
    p_page.add_argument("--begin", required=True, help="params[beginCreateTime]")
    p_page.add_argument("--end", required=True, help="params[endCreateTime]")
    p_page.add_argument("--page-num", type=int, default=1)
    p_page.add_argument("--page-size", type=int, default=50)

    p_sum = sub.add_parser("summary", help="仅拉 listAll 区间汇总")
    p_sum.add_argument("--begin", required=True)
    p_sum.add_argument("--end", required=True)

    p_full = sub.add_parser("full", help="全量拉取区间内所有订单")
    p_full.add_argument("--begin", required=True)
    p_full.add_argument("--end", required=True)
    p_full.add_argument("--page-size", type=int, default=50)
    p_full.add_argument(
        "--save-state",
        action="store_true",
        help="写入 data/goods_order_sync_state.json 供增量使用",
    )
    p_full.add_argument(
        "--compact",
        action="store_true",
        help="订单只输出核心字段",
    )

    p_inc = sub.add_parser("incremental", help="按状态文件增量拉取")
    p_inc.add_argument(
        "--end",
        default="",
        help="结束 createTime，默认当前时间",
    )
    p_inc.add_argument("--overlap-minutes", type=int, default=10)
    p_inc.add_argument("--page-size", type=int, default=50)
    p_inc.add_argument("--compact", action="store_true")

    args = parser.parse_args()
    setup_logger()
    tr = lambda b, e: GoodsOrderTimeRange(begin_create_time=b, end_create_time=e)

    if args.command == "page":
        page = list_goods_orders_page(tr(args.begin, args.end), args.page_num, args.page_size)
        out = {
            "code": page.code,
            "total": page.total,
            "rows": [r.model_dump(by_alias=True) for r in page.rows],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.command == "summary":
        s = get_goods_order_summary(tr(args.begin, args.end))
        print(json.dumps(s.model_dump(by_alias=True), ensure_ascii=False, indent=2))
        return

    if args.command == "full":
        if args.save_state:
            result = sync_goods_orders_full_and_save_state(
                tr(args.begin, args.end), page_size=args.page_size
            )
        else:
            result = sync_goods_orders_full(tr(args.begin, args.end), page_size=args.page_size)
        _print_sync_result(result, compact=args.compact)
        return

    if args.command == "incremental":
        end = args.end or None
        result = sync_goods_orders_incremental(
            end_create_time=end,
            overlap_minutes=args.overlap_minutes,
            page_size=args.page_size,
        )
        _print_sync_result(result, compact=args.compact)


def _print_sync_result(result, *, compact: bool) -> None:
    payload = result.to_dict()
    if compact:
        payload["orders"] = [
            {
                "shopOrderId": o.shop_order_id,
                "orderSn": o.order_sn,
                "createTime": o.create_time,
                "facilityName": o.facility_name,
                "goodsName": o.goods_name,
                "orderMoney": o.order_money,
                "status": o.status,
                "payType": o.pay_type,
            }
            for o in result.orders
        ]
    else:
        payload["orders"] = [o.model_dump(by_alias=True) for o in result.orders]
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
