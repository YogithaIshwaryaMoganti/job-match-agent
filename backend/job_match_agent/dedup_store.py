"""SQLite-backed dedup store — the guardrail that makes repeated runs safe.

A posting already seen in a prior run is filtered out before it ever reaches
the matching agent, so re-running this tool daily doesn't re-score, re-show,
or (if submission were ever added) re-apply to the same posting.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "seen_postings.db"


class DedupStore:
    def __init__(self, db_path: str | Path | None = None):
        db_path = Path(db_path) if db_path else Path(os.environ.get("DEDUP_DB_PATH", DEFAULT_DB_PATH))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS seen_postings (dedup_key TEXT PRIMARY KEY, first_seen_at TEXT)"
        )
        self._conn.commit()

    def filter_unseen(self, postings: list) -> list:
        """Return only postings not already recorded as seen."""
        seen_keys = {
            row[0]
            for row in self._conn.execute(
                "SELECT dedup_key FROM seen_postings WHERE dedup_key IN ({})".format(
                    ",".join("?" * len(postings))
                ),
                [p.dedup_key for p in postings],
            )
        } if postings else set()
        return [p for p in postings if p.dedup_key not in seen_keys]

    def mark_seen(self, postings: list) -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._conn.executemany(
            "INSERT OR IGNORE INTO seen_postings (dedup_key, first_seen_at) VALUES (?, ?)",
            [(p.dedup_key, now) for p in postings],
        )
        self._conn.commit()

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM seen_postings").fetchone()[0]

    def close(self) -> None:
        self._conn.close()
