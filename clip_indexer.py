#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clip_indexer.py
Scans a clips directory, computes quick fingerprints and shot metadata,
and writes it into the SQLite DB used by the project.
"""
from __future__ import annotations
import argparse
import os
import json
from pathlib import Path
from scene_fingerprint import extract_keyframe, dhash, color_histogram, shot_type_from_stats
import sqlite3
import time
import cv2

DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"


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


def index_clip(conn, path: Path):
    pstr = str(path)
    cursor = conn.cursor()
    try:
        duration = media_duration(pstr)
        keyframe = extract_keyframe(pstr)
        if keyframe is None:
            print(f"Skipping (no keyframe): {pstr}")
            return False
        fp = dhash(keyframe)
        hist = color_histogram(keyframe)
        shot = shot_type_from_stats(keyframe)
        cursor.execute("INSERT OR REPLACE INTO clips (path, filename, duration, fingerprint, shot_type, color_histogram, motion_score, added_ts) VALUES (?,?,?,?,?,?,?,?)",
                       (pstr, path.name, duration, fp, shot, json.dumps(hist), 0.5, int(time.time())))
        conn.commit()
        print(f"Indexed: {path.name} [{shot}] fp={fp[:8]}")
        return True
    except Exception as e:
        print(f"Error indexing {pstr}: {e}")
        return False


def scan_and_index(folder: str, db_path: str):
    conn = init_db(db_path)
    folder = Path(folder)
    files = [p for p in folder.rglob('*') if p.suffix.lower() in ('.mp4', '.mov', '.mkv', '.avi')]
    print(f"Found {len(files)} media files in {folder}")
    for p in files:
        index_clip(conn, p)
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--clips', required=True)
    parser.add_argument('--db', default=DEFAULT_DB)
    parser.add_argument('--reindex', action='store_true')
    args = parser.parse_args()
    scan_and_index(args.clips, args.db)
