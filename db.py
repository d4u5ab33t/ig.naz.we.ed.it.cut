#!/usr/bin/env python3
# db.py
"""
Extended WeeditDB with fields for fingerprint, color_hist, shot_type and motion.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class WeeditDB:
    def __init__(self, db_path: str = r"D:/Oidasheim/weedit/weedit_v4.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE,
                    filename TEXT,
                    duration REAL DEFAULT 0.0,
                    fingerprint TEXT DEFAULT '',
                    color_hist TEXT DEFAULT '',
                    shot_type TEXT DEFAULT '',
                    motion REAL DEFAULT 0.0,
                    tags TEXT DEFAULT '',
                    last_indexed INTEGER DEFAULT 0,
                    uses INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def upsert_clip(self, meta: Dict[str, Any]):
        # meta expected to contain path, filename, duration, motion, color_hist, shot_type, fingerprint
        import hashlib
        clip_id = hashlib.md5(meta['path'].encode('utf-8')).hexdigest()[:12]
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO clips (id, path, filename, duration, fingerprint, color_hist, shot_type, motion, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename=excluded.filename,
                    duration=CASE WHEN excluded.duration>0 THEN excluded.duration ELSE clips.duration END,
                    fingerprint=excluded.fingerprint,
                    color_hist=excluded.color_hist,
                    shot_type=excluded.shot_type,
                    motion=excluded.motion,
                    last_indexed=excluded.last_indexed
            """,
            (clip_id, meta['path'], meta.get('filename', ''), float(meta.get('duration', 0.0)), meta.get('fingerprint',''), json.dumps(meta.get('color_hist',[])), meta.get('shot_type',''), float(meta.get('motion',0.0)), int(meta.get('last_indexed',0)))
            )
            conn.commit()

    def get_all_clips(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM clips").fetchall()
            out = []
            for r in rows:
                d = dict(r)
                try:
                    d['color_hist'] = json.loads(d.get('color_hist') or '[]')
                except Exception:
                    d['color_hist'] = []
                out.append(d)
            return out

    def find_similar_shot_type(self, shot_type: str, limit: int = 200) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM clips WHERE shot_type=? ORDER BY last_indexed DESC LIMIT ?", (shot_type, limit)).fetchall()
            return [dict(r) for r in rows]

    def bump_usage(self, path: str):
        with self._conn() as conn:
            conn.execute("UPDATE clips SET uses = uses + 1, last_indexed = ? WHERE path = ?", (int(time.time()), path))
            conn.commit()
