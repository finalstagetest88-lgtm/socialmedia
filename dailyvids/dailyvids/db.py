from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  sha1 TEXT NOT NULL,
  duration_seconds REAL,
  width INTEGER,
  height INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  posted_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_media_posted_at ON media(posted_at);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def insert_media(self, items: Iterable[Dict[str, object]]) -> int:
        count = 0
        with self.connect() as conn:
            for item in items:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO media(path, sha1, duration_seconds, width, height) VALUES (?, ?, ?, ?, ?)",
                        (
                            str(item.get("path")),
                            item.get("sha1"),
                            item.get("duration_seconds"),
                            item.get("width"),
                            item.get("height"),
                        ),
                    )
                    count += 1
                except sqlite3.Error:
                    continue
            conn.commit()
        return count

    def fetch_next_unposted(self) -> Optional[Dict[str, object]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, path, sha1, duration_seconds, width, height FROM media WHERE posted_at IS NULL ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "path": row["path"],
                "sha1": row["sha1"],
                "duration_seconds": row["duration_seconds"],
                "width": row["width"],
                "height": row["height"],
            }

    def mark_posted(self, media_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE media SET posted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (media_id,),
            )
            conn.commit()

