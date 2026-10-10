from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from api_client import ApiClient
from config import Settings
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


def start_scheduler(settings: Settings) -> None:
    scheduler = BlockingScheduler(timezone=settings.schedule.timezone)

    if settings.schedule.cron:
        trigger = CronTrigger.from_crontab(
            settings.schedule.cron,
            timezone=settings.schedule.timezone,
        )
    else:
        interval = (
            settings.schedule.interval_minutes
            or settings.app.interval_minutes
            or 60
        )
        trigger = IntervalTrigger(minutes=interval, timezone=settings.schedule.timezone)

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
