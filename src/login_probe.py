"""登录探测：验证凭据并打印可读的账号/权限/设备摘要。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hfyuwo.context import create_context  # noqa: E402
from hfyuwo.services.facility import list_all_facilities  # noqa: E402
from hfyuwo.services.user import get_user_info  # noqa: E402
from logger import setup_logger  # noqa: E402
from loguru import logger  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="登录并探测后台可用数据")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "settings.yaml"),
        help="配置文件路径",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="输出完整 getInfo JSON（不含 token）",
    )
    args = parser.parse_args()

    setup_logger()
    ctx = create_context(args.config)
    token = ctx.ensure_token()
    logger.info("登录成功，Token 长度 {}", len(token))

    info = get_user_info(ctx=ctx)
    user = info.user
    summary = {
        "login": {"token_preview": f"{token[:24]}..."},
        "user": {
            "userId": user.user_id if user else None,
            "userName": user.user_name if user else None,
            "nickName": user.nick_name if user else None,
            "operatorId": user.operator_id if user else None,
            "operatorName": user.operator_name if user else None,
            "roles": info.roles,
            "permissions_count": len(info.permissions),
        },
    }

    try:
        facilities = list_all_facilities(ctx=ctx)
        summary["facilities"] = {
            "total_fetched": len(facilities),
            "sample": [
                {
                    "facilityId": f.facility_id,
                    "facilityNumber": f.facility_number,
                    "facilityName": f.facility_name,
                    "facilityType": f.facility_type,
                    "facilityConnectionStatus": f.facility_connection_status,
                    "facilityCount": f.facility_count,
                    "uploaddataTime": f.uploaddata_time,
                }
                for f in facilities[:3]
            ],
        }
    except Exception as e:
        summary["facilities_error"] = str(e)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.full:
        print("\n--- getInfo (full) ---")
        print(json.dumps(info.model_dump(by_alias=True), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
