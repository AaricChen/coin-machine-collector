"""独立 CLI：GET /vending/facility/{id} 设备详情。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hfyuwo.services.facility import get_facility_detail  # noqa: E402
from logger import setup_logger  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="获取单台设备详情")
    parser.add_argument("facility_id", type=int, help="facilityId，如 3222")
    parser.add_argument(
        "--facility-number",
        default="",
        help="facilityNumber，用于 Referer（可选）",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="隐藏 device_password 等敏感字段",
    )
    args = parser.parse_args()

    setup_logger()
    detail = get_facility_detail(
        args.facility_id,
        facility_number=args.facility_number or None,
    )
    data = detail.model_dump(by_alias=True)
    if args.compact:
        data.pop("password", None)
    print(json.dumps({"code": 200, "data": data}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
