#!/usr/bin/env python3
# scene_fingerprint.py - fast approximate scene fingerprinting, color histogram and shot-type
import cv2
import numpy as np
from pathlib import Path
import json

# fast frame sampling and downscale
SAMPLE_FRAMES = 5
DOWNSCALE = (160, 90)

def _sample_frames(path: str, max_frames: int = SAMPLE_FRAMES):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if n <= 0:
        cap.release()
        return []
    idxs = np.linspace(0, max(0, n-1), num=min(max_frames, n), dtype=int)
    frames = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, DOWNSCALE, interpolation=cv2.INTER_AREA)
        frames.append(frame)
    cap.release()
    return frames

def compute_color_histogram(path: str, bins=(8,8,8)) -> str:
    frames = _sample_frames(path, SAMPLE_FRAMES)
    if not frames:
        return json.dumps([0]* (bins[0]*bins[1]*bins[2]))
    hist = None
    for f in frames:
        h = cv2.calcHist([f], [0,1,2], None, bins, [0,256,0,256,0,256])
        h = cv2.normalize(h, h).flatten()
        hist = h if hist is None else (hist + h)
    hist = (hist / len(frames)).tolist()
    return json.dumps([float(x) for x in hist])

def compute_scene_fingerprint(path: str) -> str:
    # Simple fast fingerprint: mean RGB per sampled frame + small dct
    frames = _sample_frames(path, SAMPLE_FRAMES)
    if not frames:
        return ""
    feats = []
    for f in frames:
        mean = f.mean(axis=(0,1)) # BGR
        small = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(small, (16,16), interpolation=cv2.INTER_AREA)
        d = cv2.dct(np.float32(small))
        feats.extend(mean.tolist()[:3])
        feats.extend(d[:3,:3].flatten().tolist())
    # Quantize and hash-lite
    arr = np.array(feats)
    q = np.round(arr).astype(int).tolist()
    return "fp:" + ",".join(str(x) for x in q)

def detect_shot_type(path: str) -> str:
    # Heuristic: based on relative face size / edge density or stillness
    frames = _sample_frames(path, SAMPLE_FRAMES)
    if not frames:
        return "unknown"
    edges = []
    motions = []
    prev_gray = None
    for f in frames:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        e = cv2.Canny(gray, 50, 150)
        edges.append(e.mean())
        if prev_gray is not None and prev_gray.shape == gray.shape:
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5,3,15,3,5,1.2,0)
            mag, _ = cv2.cartToPolar(flow[...,0], flow[...,1])
            motions.append(mag.mean())
        prev_gray = gray
    edge_mean = np.mean(edges)
    motion_mean = np.mean(motions) if motions else 0.0
    # rough thresholds
    if motion_mean < 0.5 and edge_mean > 20:
        return "closeup"
    if motion_mean < 1.5 and edge_mean < 25:
        return "medium"
    return "wide"

if __name__ == '__main__':
    import sys
    p = sys.argv[1]
    print('fingerprint:', compute_scene_fingerprint(p))
    print('shot_type:', detect_shot_type(p))
    print('hist:', compute_color_histogram(p))
