#!/usr/bin/env python3
# db_indexer.py
"""
Small DB helper to migrate/ensure clip fields and provide simple queries used by indexer & renderer.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_DB = Path(r"D:/Oidasheim/weedit/weedit_v4.db")


def open_db(path: Path = DEFAULT_DB, timeout: float = 5.0) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS clips (path TEXT PRIMARY KEY, filename TEXT, duration REAL, fingerprint TEXT, color_summary TEXT, motion REAL, shot_type TEXT, tags TEXT, indexed_ts INTEGER)")
    conn.commit()


def get_clip_by_path(conn: sqlite3.Connection, path: str) -> Optional[Dict[str,Any]]:
    cur = conn.cursor()
    row = cur.execute('SELECT * FROM clips WHERE path=?', (path,)).fetchone()
    if not row:
        return None
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))


if __name__ == '__main__':
    c = open_db()
    ensure_schema(c)
    print('DB ready')
    c.close()
