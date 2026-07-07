#!/usr/bin/env python3
# clip_indexer.py
"""
Clip indexer: scans clip pools, computes fast scene fingerprints,
color histogram, shot type and motion score and stores into SQLite DB.
"""
from pathlib import Path
import os
import json
import hashlib
import time
import subprocess
from typing import List, Dict, Any

from preprocessor import VideoPreprocessor
from clip_pools import resolve_pools
from db import WeeditDB

FFPROBE = 'ffprobe'


def _ffprobe_duration(path: Path) -> float:
    try:
        r = subprocess.run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def color_histogram(path: Path, sample_frames: int = 3, bins: int = 16) -> List[float]:
    import cv2
    cap = cv2.VideoCapture(str(path))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        cap.release()
        return [0.0] * (bins * 3)
    positions = [int(frame_count * (i + 1) / (sample_frames + 1)) for i in range(sample_frames)]
    hist_acc = [0.0] * (bins * 3)
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        for c in range(3):
            hist = cv2.calcHist([frame], [c], None, [bins], [0, 256]).flatten()
            hist = hist / (hist.sum() + 1e-9)
            for i, v in enumerate(hist):
                hist_acc[c * bins + i] += float(v)
    cap.release()
    # average
    for i in range(len(hist_acc)):
        hist_acc[i] = hist_acc[i] / max(1, sample_frames)
    return [float(x) for x in hist_acc]


def shot_type_guess(path: Path, motion_score: float, duration: float) -> str:
    # Simple heuristic: aspect ratio + motion
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
    except Exception:
        w, h = 1920, 1080
    ar = w / max(1, h)
    if motion_score > 0.6:
        return 'action'
    if ar > 2.0:
        return 'ultrawide'
    if ar > 1.4:
        return 'wide'
    if ar < 0.75:
        return 'portrait'
    if duration < 1.5:
        return 'cutaway'
    return 'standard'


def fingerprint_from_features(hist: List[float], motion: float, shot_type: str) -> str:
    m = hashlib.sha1()
    payload = json.dumps({'h': hist[:8], 'm': round(motion,3), 's': shot_type}).encode('utf-8')
    m.update(payload)
    return m.hexdigest()[:16]


class ClipIndexer:
    def __init__(self, db_path: str = None, pools: List[str] | None = None):
        self.db = WeeditDB(db_path) if db_path else WeeditDB()
        self.pools = pools or resolve_pools()
        self.vproc = VideoPreprocessor()

    def index_file(self, p: str) -> Dict[str, Any]:
        path = Path(p)
        if not path.exists():
            return {}
        duration = _ffprobe_duration(path)
        motion = self.vproc.analyze_motion_score(str(path), samples=5)
        hist = color_histogram(path, sample_frames=3, bins=16)
        shot = shot_type_guess(path, motion, duration)
        fingerprint = fingerprint_from_features(hist, motion, shot)
        entry = {
            'path': str(path),
            'filename': path.name,
            'duration': float(duration),
            'motion': float(motion),
            'color_hist': hist,
            'shot_type': shot,
            'fingerprint': fingerprint,
            'last_indexed': int(time.time())
        }
        self.db.upsert_clip(entry)
        return entry

    def index_all(self, reindex: bool = False) -> int:
        files = []
        for pool in self.pools:
            for root, dirs, filenames in os.walk(pool):
                for fn in filenames:
                    if fn.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
                        files.append(os.path.join(root, fn))
        count = 0
        for f in files:
            try:
                self.index_file(f)
                count += 1
            except Exception:
                pass
        return count


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reindex', action='store_true')
    parser.add_argument('--db', type=str, help='db path')
    args = parser.parse_args()
    idx = ClipIndexer(db_path=args.db)
    n = idx.index_all(reindex=args.reindex)
    print(f"Indexed {n} clips")
