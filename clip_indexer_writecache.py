#!/usr/bin/env python3
# clip_indexer.py (follow-up) - write cache after indexing
from pathlib import Path
import argparse
import json
import sqlite3
import sys

from scene_fingerprint import frame_dhash, dominant_color, color_histogram_summary, estimate_motion_score
from cache_manager import save_cache

from db import WeeditDB

DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"
DEFAULT_CACHE = r"D:/Oidasheim/weedit/weedit_clip_cache.json"

# reusing earlier index logic but writing cache

def index_dir_and_write_cache(folder: str, db_path: str = DEFAULT_DB, cache_path: str = DEFAULT_CACHE, limit: int = 0):
    db = WeeditDB(db_path)
    files = list(Path(folder).rglob('*'))
    files = [p for p in files if p.is_file() and p.suffix.lower() in ('.mp4','.mov','.mkv','.avi','.webm')]
    if limit and limit > 0:
        files = files[:limit]
    out = []
    for p in files:
        try:
            from clip_indexer import index_clip as ic
            # index_clip previously returns metadata when successful
            # we call through clip_indexer.index_clip (if present), else replicate minimal
            # to avoid circular import, call DB upsert directly
            # Here assume clip_indexer.index_clip exists in repo; if not, skip
            res = None
            try:
                import clip_indexer as CI
                conn = CI.ensure_db(Path(db_path))
                res = CI.index_clip(conn, p, force=True)
                conn.close()
            except Exception:
                # fallback to simple metadata
                res = {'path': str(p), 'filename': p.name}
            if res:
                out.append(res)
        except Exception:
            continue
    # write cache
    save_cache(out, cache_path)
    print(f"Wrote cache {len(out)} entries -> {cache_path}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', '-d', required=True)
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--cache', default=DEFAULT_CACHE)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    index_dir_and_write_cache(args.dir, args.db, args.cache, args.limit)

if __name__ == '__main__':
    main()
