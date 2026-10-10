import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import load_config  # noqa: E402
from logger import setup_logger  # noqa: E402
from loguru import logger  # noqa: E402
from scheduler import run_collection_job, start_scheduler  # noqa: E402


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
        choices=["once", "schedule"],
        default=None,
        help="运行模式，覆盖配置文件中的选择",
    )
    args = parser.parse_args()

    setup_logger()
    settings = load_config(args.config)
    if args.mode:
        settings.app.run_mode = args.mode

    logger.info("启动模式：{}", settings.app.run_mode)
    if settings.app.run_mode == "once":
        run_collection_job(settings)
    else:
        start_scheduler(settings)


if __name__ == "__main__":
    main()
