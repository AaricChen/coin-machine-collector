"""独立 CLI：拉取 vending/facility/list 设备列表。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hfyuwo.services.facility import list_all_facilities, list_facilities_page  # noqa: E402
from logger import setup_logger  # noqa: E402
from loguru import logger  # noqa: E402


def _serialize_page(page, *, compact: bool) -> dict:
    rows = page.rows
    if compact:
        rows = [
            {
                "facilityId": f.facility_id,
                "facilityNumber": f.facility_number,
                "facilityName": f.facility_name,
                "facilityType": f.facility_type,
                "facilityConnectionStatus": f.facility_connection_status,
                "facilityMachineStatus": f.facility_machine_status,
                "facilityCount": f.facility_count,
                "operatorName": f.operator_name,
                "operatorPhone": f.operator_phone,
                "uploaddataTime": f.uploaddata_time,
                "expirationTime": f.expiration_time,
                "facilityAddress": f.facility_address,
            }
            for f in rows
        ]
    else:
        rows = [f.model_dump(by_alias=True) for f in rows]
    return {
        "code": page.code,
        "msg": page.msg,
        "total": page.total,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="调用 /vending/facility/list 获取纪念币机设备列表",
    )
    parser.add_argument("--page-num", type=int, default=1, help="页码，从 1 开始")
    parser.add_argument("--page-size", type=int, default=50, help="每页条数")
    parser.add_argument(
        "--all",
        action="store_true",
        help="拉取全部页（按 total 自动翻页）",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="只输出常用字段摘要",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="输出接口完整字段（等同未加 --compact）",
    )
    args = parser.parse_args()

    setup_logger()
    compact = args.compact and not args.raw

    if args.all:
        logger.info("拉取全部设备（pageSize={}）", args.page_size)
        facilities = list_all_facilities(page_size=args.page_size)
        from hfyuwo.models.base import RuoYiPage

        page = RuoYiPage(
            code=200,
            msg="查询成功",
            total=len(facilities),
            rows=facilities,
        )
    else:
        logger.info("拉取第 {} 页（pageSize={}）", args.page_num, args.page_size)
        page = list_facilities_page(args.page_num, args.page_size)

    print(json.dumps(_serialize_page(page, compact=compact), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
