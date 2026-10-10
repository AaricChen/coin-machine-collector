"""登录探测：验证凭据并打印可读的账号/权限/设备摘要。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from api_client import ApiClient  # noqa: E402
from config import load_config  # noqa: E402
from logger import setup_logger  # noqa: E402
from loguru import logger  # noqa: E402
from token_manager import TokenManager  # noqa: E402


def _summarize_user(info: dict) -> dict:
    user = info.get("user") or {}
    return {
        "userId": user.get("userId"),
        "userName": user.get("userName"),
        "nickName": user.get("nickName"),
        "operatorId": user.get("operatorId"),
        "operatorName": user.get("operatorName"),
        "roles": info.get("roles"),
        "permissions_count": len(info.get("permissions") or []),
    }


def _summarize_facility(row: dict) -> dict:
    return {
        "facilityId": row.get("facilityId"),
        "facilityNumber": row.get("facilityNumber"),
        "facilityName": row.get("facilityName"),
        "facilityType": row.get("facilityType"),
        "facilityConnectionStatus": row.get("facilityConnectionStatus"),
        "facilityCount": row.get("facilityCount"),
        "uploaddataTime": row.get("uploaddataTime"),
    }


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
    settings = load_config(args.config)
    token_manager = TokenManager(settings)
    token = token_manager.get_valid_token()
    logger.info("登录成功，Token 长度 {}", len(token))

    client = ApiClient(settings, token_manager)
    info = client.get_user_info()
    summary = {
        "login": {"token_preview": f"{token[:24]}..."},
        "user": _summarize_user(info),
    }

    try:
        machines = client.get_machine_list()
        summary["facilities"] = {
            "total_fetched": len(machines),
            "sample": [_summarize_facility(m) for m in machines[:3]],
        }
    except Exception as e:
        summary["facilities_error"] = str(e)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.full:
        print("\n--- getInfo (full) ---")
        print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
