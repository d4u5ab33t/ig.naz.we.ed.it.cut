#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Updated db.py: adds fingerprint, shot_type, color_histogram support

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sqlite3
import hashlib
import time
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
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE,
                    filename TEXT,
                    duration REAL DEFAULT 0.0,
                    fingerprint TEXT DEFAULT '',
                    color_histogram TEXT DEFAULT '',
                    shot_type TEXT DEFAULT '',
                    vibe_9d TEXT DEFAULT '[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]',
                    tags TEXT DEFAULT '',
                    uses INTEGER DEFAULT 0,
                    last_used REAL DEFAULT 0.0
                )
            """)
            conn.commit()

    def sync_cache_json(self, json_path: str):
        p = Path(json_path)
        if not p.exists(): return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with self._conn() as conn:
                for path, meta in data.items():
                    clip_id = hashlib.md5(path.encode('utf-8')).hexdigest()[:12]
                    raw_emb = meta.get("embedding", [])
                    if not isinstance(raw_emb, list): raw_emb = []
                    emb = [float(x) for x in raw_emb[:9]]
                    if len(emb) < 9: emb += [0.0] * (9 - len(emb))
                    vibe_json = json.dumps(emb)
                    fingerprint = meta.get('fingerprint', '')
                    hist = json.dumps(meta.get('color_histogram', []))
                    shot = meta.get('shot_type', '')
                    conn.execute("""
                        INSERT INTO clips (id, path, filename, duration, fingerprint, color_histogram, shot_type, vibe_9d, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(path) DO UPDATE SET 
                            vibe_9d=excluded.vibe_9d,
                            filename=excluded.filename,
                            duration=CASE WHEN excluded.duration > 0 THEN excluded.duration ELSE clips.duration END,
                            fingerprint=excluded.fingerprint,
                            color_histogram=excluded.color_histogram,
                            shot_type=excluded.shot_type
                    """, (clip_id, path, Path(path).name, float(meta.get("duration", 0.0)), fingerprint, hist, shot, vibe_json, ""))
                conn.commit()
        except Exception as e:
            print(f"⚠️ [DB] Sync-Fehler: {e}")

    def register_clip(self, path: str, duration: float = 0.0, fingerprint: str = '', color_hist: Optional[List[float]] = None, shot_type: str = ''):
        clip_id = hashlib.md5(path.encode('utf-8')).hexdigest()[:12]
        hist_json = json.dumps(color_hist or [])
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO clips (id, path, filename, duration, fingerprint, color_histogram, shot_type) VALUES (?,?,?,?,?,?,?)",
                         (clip_id, path, Path(path).name, float(duration), fingerprint, hist_json, shot_type))
            conn.commit()

    def get_all_clips(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM clips")
            return [dict(row) for row in cursor.fetchall()]

    def get_clip_metadata(self, path: str) -> Dict[str, Any]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT fingerprint, color_histogram, shot_type FROM clips WHERE path=?", (path,)).fetchone()
            if not r:
                return {}
            return {'fingerprint': r['fingerprint'], 'color_histogram': json.loads(r['color_histogram']) if r['color_histogram'] else [], 'shot_type': r['shot_type']}

    def increment_clip_usage(self, clip_id: str):
        with self._conn() as conn:
            conn.execute("UPDATE clips SET uses = uses + 1, last_used = ? WHERE id = ?", (time.time(), clip_id))
            conn.commit()
