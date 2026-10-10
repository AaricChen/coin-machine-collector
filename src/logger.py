import sys
from pathlib import Path

from loguru import logger

from paths import PROJECT_ROOT


def setup_logger() -> None:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | {message}"
        ),
        level="INFO",
    )
    logger.add(
        log_dir / "collector_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
    )
