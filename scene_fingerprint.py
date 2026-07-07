#!/usr/bin/env python3
# scene_fingerprint.py
"""
Utilities for fast scene fingerprint and shot-type detection.
Designed to be approximate and fast (no heavy ML).
"""
from pathlib import Path
import numpy as np
import cv2


def frame_tiles_mean(frame, tiles=(4,4)):
    h,w,_ = frame.shape
    th = h//tiles[0]
    tw = w//tiles[1]
    out = []
    for r in range(tiles[0]):
        for c in range(tiles[1]):
            tile = frame[r*th:(r+1)*th, c*tw:(c+1)*tw]
            out.append(float(tile.mean()))
    return np.array(out, dtype=np.float32)


def fast_fingerprint(path: Path, max_frames=5):
    cap = cv2.VideoCapture(str(path))
    fcount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fcount <=0:
        cap.release()
        return []
    step = max(1, fcount//(max_frames+1))
    feats = []
    for i in range(1, max_frames+1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i*step)
        ret, frame = cap.read()
        if not ret: break
        feat = frame_tiles_mean(frame, tiles=(4,4))
        feats.append(feat)
    cap.release()
    if not feats:
        return []
    feats = np.stack(feats)
    # compress to small vector
    v = feats.mean(axis=0)
    v = (v - v.mean()) / (v.std() + 1e-9)
    return v.tolist()
