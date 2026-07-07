#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scene_fingerprint.py
Fast approximate scene fingerprinting & helpers:
- keyframe extraction
- perceptual hash (dhash)
- small HSV color histogram
- quick shot_type heuristic
"""
from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path


def extract_keyframe(video_path: str, frame_idx: int = None):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        return None
    if frame_idx is None:
        frame_idx = frame_count // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_idx, frame_count - 1))
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return frame


def dhash(image: np.ndarray, hash_size: int = 8) -> str:
    # difference hash (grayscale)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = small[:, 1:] > small[:, :-1]
    # convert to hex string
    dh = 0
    h = 0
    for v in diff.flatten():
        dh = (dh << 1) | int(v)
    return f"{dh:0{hash_size*hash_size//4}x}"


def color_histogram(image: np.ndarray, bins=(8, 8, 4)) -> list:
    # compute HSV histogram normalized
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, bins, [0, 180, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten().tolist()


def shot_type_from_stats(image: np.ndarray, motion_score: float = None) -> str:
    # Very coarse heuristic: use edge density and motion_score
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = edges.mean()
    if motion_score is not None:
        if motion_score > 0.6 or edge_density > 20:
            return 'action'
        else:
            return 'static'
    else:
        return 'action' if edge_density > 20 else 'static'


if __name__ == '__main__':
    import sys, json
    p = sys.argv[1] if len(sys.argv) > 1 else None
    if not p:
        print('Usage: scene_fingerprint.py <video>')
        raise SystemExit(1)
    img = extract_keyframe(p)
    if img is None:
        print('failed')
        raise SystemExit(2)
    out = {
        'dhash': dhash(img),
        'hist': color_histogram(img)[:16],
        'shot_type': shot_type_from_stats(img)
    }
    print(json.dumps(out))
