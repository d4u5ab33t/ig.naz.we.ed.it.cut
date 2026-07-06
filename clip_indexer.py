#!/usr/bin/env python3
# clip_indexer.py - scans clip pools, computes fingerprints, shot type and color histogram, writes to DB
import os
import json
import time
import sqlite3
import logging
from pathlib import Path
from typing import Optional

from db import WeeditDB
from clip_pools import resolve_pools
from scene_fingerprint import compute_scene_fingerprint, compute_color_histogram, detect_shot_type

LOG = logging.getLogger("weedit.indexer")

VIDEO_EXTS = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v'}

class ClipIndexer:
    def __init__(self, db_path: str = None):
        self.db = WeeditDB(db_path) if db_path else WeeditDB()
        self._last_scan = 0

    def scan_pools(self, force: bool = False):
        pools = resolve_pools(verbose=True)
        changed = 0
        for pool in pools:
            for root, _dirs, files in os.walk(pool):
                for fn in files:
                    if Path(fn).suffix.lower() not in VIDEO_EXTS:
                        continue
                    p = os.path.join(root, fn)
                    try:
                        if self._needs_index(p) or force:
                            self.index_path(p)
                            changed += 1
                    except Exception as exc:
                        LOG.warning("Index error %s: %s", p, exc)
        self._last_scan = time.time()
        LOG.info("Index complete (%d updated)", changed)
        return changed

    def _needs_index(self, path: str) -> bool:
        try:
            st = Path(path).stat()
        except Exception:
            return False
        mtime = int(st.st_mtime)
        row = self.db.get_clip_by_path(path)
        if not row:
            return True
        return row.get('mtime_ms', 0) != mtime

    def index_path(self, path: str):
        LOG.info("Indexing %s", path)
        try:
            fp = compute_scene_fingerprint(path)
            hist = compute_color_histogram(path)
            shot = detect_shot_type(path)
            duration = self._probe_duration(path)
            mtime = int(Path(path).stat().st_mtime)
            self.db.upsert_clip_metadata(path, duration=duration, fingerprint=fp, shot_type=shot, color_hist=hist, mtime_ms=mtime)
            LOG.info("Indexed %s (shot=%s)", Path(path).name, shot)
        except Exception as e:
            LOG.exception("Failed to index %s: %s", path, e)

    def _probe_duration(self, path: str) -> float:
        try:
            import subprocess, json
            r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json", path], capture_output=True, text=True)
            return float(json.loads(r.stdout)['format']['duration'])
        except Exception:
            return 0.0

    def reindex_if_needed(self, interval: int = 60):
        if time.time() - self._last_scan > interval:
            return self.scan_pools()
        return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    idx = ClipIndexer()
    idx.scan_pools(force=True)
