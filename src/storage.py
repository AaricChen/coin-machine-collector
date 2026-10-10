import json
import sqlite3
from pathlib import Path
from typing import Any

from loguru import logger

from paths import PROJECT_ROOT


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS machine_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT NOT NULL,
                    machine_name TEXT,
                    track_id TEXT,
                    track_name TEXT,
                    stock INTEGER,
                    capacity INTEGER,
                    collection_time TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_machine_collection
                ON machine_snapshot(machine_id, collection_time)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _spill_to_json(self, records: list[dict[str, Any]]) -> None:
        spill_dir = PROJECT_ROOT / "data" / "failed_writes"
        spill_dir.mkdir(parents=True, exist_ok=True)
        path = spill_dir / f"records_{records[0].get('collection_time', 'unknown')}.json"
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.error("写入失败，已备份 {} 条记录到 {}", len(records), path)

    def save_records(self, records: list[dict[str, Any]]) -> None:
        if not records:
            logger.warning("没有数据可写入，跳过")
            return

        conn = self._get_conn()
        try:
            conn.executemany(
                """
                INSERT INTO machine_snapshot
                (machine_id, machine_name, track_id, track_name, stock, capacity, collection_time)
                VALUES
                (:machine_id, :machine_name, :track_id, :track_name, :stock, :capacity, :collection_time)
                """,
                records,
            )
            conn.commit()
            logger.info("成功写入 {} 条记录到数据库", len(records))
        except Exception as e:
            conn.rollback()
            logger.exception("写入数据库失败：{}", e)
            self._spill_to_json(records)
            raise
        finally:
            conn.close()
