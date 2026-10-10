import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import load_config  # noqa: E402
from logger import setup_logger  # noqa: E402
from loguru import logger  # noqa: E402
from scheduler import (  # noqa: E402
    run_collection_job,
    run_ops_sync_job,
    start_ops_scheduler,
    start_scheduler,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="纪念币机后台数据采集工具")
    default_config = ROOT / "config" / "settings.yaml"
    parser.add_argument(
        "--config",
        default=str(default_config),
        help="配置文件路径",
    )
    parser.add_argument(
        "--mode",
        choices=["once", "schedule", "ops-once", "ops-schedule"],
        default=None,
        help="运行模式，覆盖配置文件中的选择",
    )
    args = parser.parse_args()

    setup_logger()
    settings = load_config(args.config)
    if args.mode:
        settings.app.run_mode = args.mode

    mode = settings.app.run_mode
    logger.info("启动模式：{}", mode)

    if mode == "once":
        run_collection_job(settings)
    elif mode == "schedule":
        start_scheduler(settings)
    elif mode == "ops-once":
        run_ops_sync_job(settings)
    elif mode == "ops-schedule":
        start_ops_scheduler(settings)
    else:
        raise SystemExit(f"未知运行模式：{mode}")


if __name__ == "__main__":
    main()
