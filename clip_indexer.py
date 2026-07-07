#!/usr/bin/env python3
"""
Updated clip_indexer to build a small cache JSON and optional Annoy index.
"""
from __future__ import annotations
import argparse
import os
import json
from pathlib import Path
import sqlite3
import time
import cv2

from scene_fingerprint import extract_keyframe, dhash, color_histogram, shot_type_from_stats
from ann_index import build_annoy_index

DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"
CACHE_JSON = r"D:/Oidasheim/weedit/weedit_clip_cache.json"
ANNOY_PREFIX = r"D:/Oidasheim/weedit/weedit_color_index"


def media_duration(path: str) -> float:
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return 0.0
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
        if frames <= 0:
            return 0.0
        return frames / fps
    except Exception:
        return 0.0


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            path TEXT PRIMARY KEY,
            filename TEXT,
            duration REAL DEFAULT 0.0,
            fingerprint TEXT DEFAULT '',
            shot_type TEXT DEFAULT '',
            color_histogram TEXT DEFAULT '',
            motion_score REAL DEFAULT 0.5,
            tags TEXT DEFAULT '',
            uses INTEGER DEFAULT 0,
            added_ts REAL DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def index_clip(conn, path: Path, cache: dict):
    pstr = str(path)
    try:
        duration = media_duration(pstr)
        keyframe = extract_keyframe(pstr)
        if keyframe is None:
            print(f"Skipping (no keyframe): {pstr}")
            return False
        fp = dhash(keyframe)
        hist = color_histogram(keyframe)
        shot = shot_type_from_stats(keyframe)
        motion = 0.5
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO clips (path, filename, duration, fingerprint, shot_type, color_histogram, motion_score, added_ts) VALUES (?,?,?,?,?,?,?,?)",
                       (pstr, path.name, duration, fp, shot, json.dumps(hist), motion, int(time.time())))
        conn.commit()
        cache[pstr] = {'duration': duration, 'fingerprint': fp, 'shot_type': shot, 'color_hist': hist, 'motion': motion}
        print(f"Indexed: {path.name} [{shot}] fp={fp[:8]}")
        return True
    except Exception as e:
        print(f"Error indexing {pstr}: {e}")
        return False


def scan_and_index(folder: str, db_path: str, cache_out: str = CACHE_JSON, build_annoy: bool = True):
    conn = init_db(db_path)
    folder = Path(folder)
    files = [p for p in folder.rglob('*') if p.suffix.lower() in ('.mp4', '.mov', '.mkv', '.avi')]
    print(f"Found {len(files)} media files in {folder}")
    cache = {}
    for p in files:
        index_clip(conn, p, cache)
    # write cache
    try:
        Path(cache_out).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_out, 'w', encoding='utf-8') as f:
            json.dump(cache, f)
        print(f"Wrote cache json: {cache_out}")
    except Exception as e:
        print(f"Failed writing cache: {e}")
    # build annoy
    try:
        if build_annoy:
            ok = build_annoy_index(cache_out, ANNOY_PREFIX)
            print('Annoy index built:', ok)
    except Exception as e:
        print('Annoy build failed:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clips', required=True)
    parser.add_argument('--db', default=DEFAULT_DB)
    parser.add_argument('--cache', default=CACHE_JSON)
    parser.add_argument('--no-ann', dest='build_ann', action='store_false')
    args = parser.parse_args()
    scan_and_index(args.clips, args.db, cache_out=args.cache, build_annoy=args.build_ann)
