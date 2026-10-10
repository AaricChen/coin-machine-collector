from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from api_client import ApiClient
from config import Settings
from hfyuwo.ops.sync import run_scheduled_ops_sync
from storage import Storage
from token_manager import TokenManager


def run_collection_job(settings: Settings) -> list[dict] | None:
    token_manager = TokenManager(settings)
    api_client = ApiClient(settings, token_manager)
    storage = Storage(settings.db_path_resolved)

    try:
        records = api_client.collect_all()
        storage.save_records(records)
        logger.success("本次采集任务完成")
        return records
    except Exception as e:
        logger.exception("采集任务失败：{}", e)
        return None


def run_ops_sync_job(settings: Settings):
    """定时入口：仅调用已封装的运维同步函数，无额外业务逻辑。"""
    try:
        return run_scheduled_ops_sync(settings)
    except Exception as e:
        logger.exception("运维同步任务失败：{}", e)
        return None


def _build_trigger(settings: Settings):
    if settings.schedule.cron:
        return CronTrigger.from_crontab(
            settings.schedule.cron,
            timezone=settings.schedule.timezone,
        )
    interval = (
        settings.schedule.interval_minutes
        or settings.app.interval_minutes
        or 60
    )
    return IntervalTrigger(minutes=interval, timezone=settings.schedule.timezone)


def start_scheduler(settings: Settings) -> None:
    scheduler = BlockingScheduler(timezone=settings.schedule.timezone)
    trigger = _build_trigger(settings)

    scheduler.add_job(
        run_collection_job,
        trigger,
        args=[settings],
        id="coin_machine_job",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    logger.info("定时任务已启动，触发器配置：{}", trigger)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已停止")


def start_ops_scheduler(settings: Settings) -> None:
    scheduler = BlockingScheduler(timezone=settings.schedule.timezone)
    trigger = _build_trigger(settings)

    scheduler.add_job(
        run_ops_sync_job,
        trigger,
        args=[settings],
        id="coin_machine_ops_job",
        misfire_grace_time=3600,
        replace_existing=True,
    )

    logger.info("运维同步定时任务已启动，触发器配置：{}", trigger)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("运维同步定时任务已停止")
