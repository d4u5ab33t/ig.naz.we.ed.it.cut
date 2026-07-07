#!/usr/bin/env python3
# db.py - extended with defaults copy and helper methods
import sqlite3
import json
import hashlib
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = Path(r"D:/Oidasheim/weedit/weedit_v4.db")
DEFAULT_DB_CANDIDATES = [
    Path('default.clip.db'),
    Path('default.songs.db')
]
FAVS_SRC_GLOBS = [
    Path(r"D:/Oidasheim/weedit").glob('FAVs*.html')
]
FAVS_TARGET = Path('./date/FAVS.html')

class WeeditDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_default_db()
        self._init_db()

    def _ensure_default_db(self):
        # If DB missing, attempt to copy from default candidates
        if self.db_path.exists():
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        for cand in DEFAULT_DB_CANDIDATES:
            if cand.exists():
                try:
                    shutil.copy(cand, self.db_path)
                    print(f"Copied default DB {cand} -> {self.db_path}")
                    return
                except Exception as e:
                    print(f"Failed to copy default DB {cand}: {e}")
        # If no default DB found, create empty DB on first init (will create schema)
        print(f"No default DB found; creating new DB at {self.db_path}")

        # Copy any FAVs HTML into training pool (best-effort)
        try:
            FAVS_TARGET.parent.mkdir(parents=True, exist_ok=True)
            for globiter in FAVS_SRC_GLOBS:
                for f in globiter:
                    try:
                        shutil.copy(f, FAVS_TARGET)
                        print(f"Copied favs: {f} -> {FAVS_TARGET}")
                        break
                    except Exception:
                        continue
        except Exception:
            pass

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
        # run migrations to add any missing columns
        self.ensure_schema_migrations()

    def ensure_schema_migrations(self):
        with self._conn() as conn:
            cur = conn.cursor()
            cols = {r[1] for r in conn.execute("PRAGMA table_info(clips)").fetchall()}
            if 'fingerprint' not in cols:
                cur.execute("ALTER TABLE clips ADD COLUMN fingerprint TEXT DEFAULT ''")
            if 'color_hist' not in cols:
                cur.execute("ALTER TABLE clips ADD COLUMN color_hist TEXT DEFAULT ''")
            if 'shot_type' not in cols:
                cur.execute("ALTER TABLE clips ADD COLUMN shot_type TEXT DEFAULT ''")
            if 'motion' not in cols:
                cur.execute("ALTER TABLE clips ADD COLUMN motion REAL DEFAULT 0.0")
            if 'last_indexed' not in cols:
                cur.execute("ALTER TABLE clips ADD COLUMN last_indexed INTEGER DEFAULT 0")
            conn.commit()

    def upsert_clip_metadata(self, path: str, duration: float = 0.0,
                             fingerprint: str = '', shot_type: str = '',
                             color_hist: Optional[List[float]] = None,
                             motion: float = 0.0, mtime_ms: Optional[int] = None):
        import hashlib
        clip_id = hashlib.md5(path.encode('utf-8')).hexdigest()[:12]
        ch_json = json.dumps(color_hist) if color_hist is not None else ''
        mtime_ms = int(mtime_ms) if mtime_ms is not None else int(time.time())
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO clips (id, path, filename, duration, fingerprint, color_hist, shot_type, motion, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename=excluded.filename,
                    duration=CASE WHEN excluded.duration>0 THEN excluded.duration ELSE clips.duration END,
                    fingerprint=COALESCE(NULLIF(excluded.fingerprint,''), clips.fingerprint),
                    color_hist=COALESCE(NULLIF(excluded.color_hist,''), clips.color_hist),
                    shot_type=COALESCE(NULLIF(excluded.shot_type,''), clips.shot_type),
                    motion=CASE WHEN excluded.motion>0 THEN excluded.motion ELSE clips.motion END,
                    last_indexed=CASE WHEN excluded.last_indexed>0 THEN excluded.last_indexed ELSE clips.last_indexed END
            """,
            (clip_id, path, Path(path).name, float(duration), fingerprint, ch_json, shot_type, float(motion), mtime_ms))
            conn.commit()

    def get_clip_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM clips WHERE path = ?", (path,)).fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d['color_hist'] = json.loads(d.get('color_hist') or '[]')
            except Exception:
                d['color_hist'] = []
            return d

    def get_all_clips(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM clips ORDER BY last_indexed DESC").fetchall()
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
            rows = conn.execute("SELECT * FROM clips WHERE shot_type = ? ORDER BY last_indexed DESC LIMIT ?", (shot_type, limit)).fetchall()
            return [dict(r) for r in rows]

    def find_by_fingerprint(self, fingerprint: str, max_hamming: int = 8) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT path,fingerprint FROM clips WHERE fingerprint != ''").fetchall()
            out = []
            tgt = fingerprint or ''
            for r in rows:
                other = r['fingerprint'] or ''
                try:
                    x = int(tgt, 16) ^ int(other, 16)
                    ham = bin(x).count('1')
                except Exception:
                    ham = 999
                if ham <= max_hamming:
                    out.append(self.get_clip_by_path(r['path']))
            return out

    def bump_usage(self, path: str):
        with self._conn() as conn:
            conn.execute("UPDATE clips SET uses = uses + 1, last_indexed = ? WHERE path = ?", (int(time.time()), path))
            conn.commit()
