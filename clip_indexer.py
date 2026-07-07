#!/usr/bin/env python3
# clip_indexer.py
"""
Lightweight clip indexer for WEEDIT Phase‑3
- Scans a set of clip pool paths (local + network aliases)
- Computes fast scene fingerprints and color histogram summary
- Estimates motion / shot_type
- Stores results in a sqlite DB (creates schema if missing)

Usage:
    python clip_indexer.py --dir D:\raw_vidz\grok --db D:/Oidasheim/weedit/weedit_v4.db --reindex
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np

from scene_fingerprint import frame_dhash, dominant_color, color_histogram_summary, estimate_motion_score

DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"
SUPPORTED_EXTS = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.mpg', '.mp4'}


def ensure_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("CREATE TABLE IF NOT EXISTS clips ("
                "path TEXT PRIMARY KEY, filename TEXT, duration REAL, "
                "fingerprint TEXT, color_summary TEXT, motion REAL, shot_type TEXT, tags TEXT, indexed_ts INTEGER)")
    conn.commit()
    return conn


def ffprobe_duration(path: Path, timeout: int = 8) -> float:
    try:
        out = subprocess.run([
            'ffprobe','-v','error','-show_entries','format=duration',
            '-of','default=noprint_wrappers=1:nokey=1', str(path)
        ], capture_output=True, text=True, timeout=timeout)
        if out.returncode == 0 and out.stdout:
            return float(out.stdout.strip())
    except Exception:
        pass
    return 0.0


def scan_folder(folder: Path) -> List[Path]:
    if not folder.exists():
        return []
    files: List[Path] = []
    for p in folder.rglob('*'):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            files.append(p)
    return sorted(files)


def classify_shot(motion_score: float, dom_color: Tuple[int,int,int]) -> str:
    # Simple rule-based shot typing
    r,g,b = dom_color
    brightness = (r+g+b)/3.0
    if motion_score > 0.6:
        return 'action'
    if motion_score > 0.25:
        return 'dynamic'
    if brightness < 40:
        return 'dark'
    if brightness > 200:
        return 'bright'
    return 'steady'


def index_clip(conn: sqlite3.Connection, clip_path: Path, force: bool = False) -> Optional[Dict]:
    cur = conn.cursor()
    key = str(clip_path)
    if not force:
        row = cur.execute('SELECT indexed_ts FROM clips WHERE path=?', (key,)).fetchone()
        if row:
            return None

    # Try to open video and analyze a few frames
    try:
        cap = cv2.VideoCapture(str(clip_path))
        if not cap.isOpened():
            cap.release()
            return None
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        dur = float(cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
        # Prefer ffprobe fallback for exact duration
        duration = ffprobe_duration(clip_path) or 0.0

        # Choose frames: start, middle, end
        frames = []
        picks = [0, max(0, frame_count//2), max(0, frame_count-1)]
        for p in picks:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(p))
            ret, f = cap.read()
            if not ret:
                continue
            frames.append(f)
        cap.release()

        if not frames:
            return None

        # Fingerprint from middle frame
        mid = frames[len(frames)//2]
        fp = frame_dhash(mid)
        domc = dominant_color(mid)
        hist_summary = color_histogram_summary(mid)
        motion = estimate_motion_score(frames)
        shot_type = classify_shot(motion, domc)

        cur.execute('INSERT OR REPLACE INTO clips (path, filename, duration, fingerprint, color_summary, motion, shot_type, tags, indexed_ts) VALUES (?,?,?,?,?,?,?,?,strftime("%s","now"))', (
            key, clip_path.name, float(duration), fp, hist_summary, float(motion), shot_type, '',
        ))
        conn.commit()
        return {'path': key, 'duration': duration, 'fingerprint': fp, 'color_summary': hist_summary, 'motion': motion, 'shot_type': shot_type}

    except Exception as e:
        print(f"[index_clip] Failed {clip_path}: {e}")
        return None


def reindex_dir(folder: Path, db_path: Path, force: bool = False):
    conn = ensure_db(db_path)
    files = scan_folder(folder)
    print(f"Found {len(files)} clips in {folder}")
    for i, f in enumerate(files, 1):
        sys.stdout.write(f"Indexing {i}/{len(files)}: {f.name}... ")
        sys.stdout.flush()
        res = index_clip(conn, f, force=force)
        print('OK' if res else 'SKIP')
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', '-d', type=str, required=True)
    parser.add_argument('--db', type=str, default=DEFAULT_DB)
    parser.add_argument('--reindex', action='store_true')
    args = parser.parse_args()
    folder = Path(args.dir)
    reindex_dir(folder, Path(args.db), force=args.reindex)


if __name__ == '__main__':
    main()
