"""独立 CLI：GET /vending/track/share/{facilityId} 配货/货道库存。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hfyuwo.services.track import get_facility_track_share  # noqa: E402
from logger import setup_logger  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="获取设备货道配货与库存信息")
    parser.add_argument("facility_id", type=int, help="facilityId，如 3222")
    parser.add_argument(
        "--tracks-only",
        action="store_true",
        help="不输出 data.facility，仅货道列表",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="货道只保留库存/商品等核心字段",
    )
    args = parser.parse_args()

    setup_logger()
    share = get_facility_track_share(args.facility_id)

    if args.compact:
        tracks = [
            {
                "trackId": t.track_id,
                "trackNumber": t.track_number,
                "goodsName": t.goods_name,
                "trackExistingCount": t.track_existing_count,
                "trackCount": t.track_count,
                "trackGoodsPrice": t.track_goods_price,
                "trackStatus": t.track_status,
            }
            for t in share.tracks
        ]
    else:
        tracks = [t.model_dump(by_alias=True) for t in share.tracks]

    out: dict = {"code": 200, "tracks": tracks}
    if not args.tracks_only and share.facility:
        out["facility"] = share.facility.model_dump(by_alias=True)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
