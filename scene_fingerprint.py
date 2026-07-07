#!/usr/bin/env python3
# scene_fingerprint.py
"""
Fast scene fingerprint utilities (no heavy deps)
- frame_dhash: perceptual dHash on grayscale 9x8
- dominant_color: kmeans=1 -> centroid
- color_histogram_summary: coarse HSV histogram quantized to string
- estimate_motion_score: simple mean frame-diff normalized
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import Tuple, List


def _resize_for_hash(img, w=9, h=8):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (w, h), interpolation=cv2.INTER_AREA)
    return small


def frame_dhash(img) -> str:
    """Compute difference hash (dHash) for a frame and return hex string."""
    try:
        small = _resize_for_hash(img, 9, 8)
        diff = small[:, 1:] > small[:, :-1]
        # Convert to hex
        bit_string = ''.join('1' if x else '0' for x in diff.flatten())
        hexstr = '{:0{}x}'.format(int(bit_string, 2), len(bit_string) // 4)
        return hexstr
    except Exception:
        return ''


def dominant_color(img, k=3) -> Tuple[int,int,int]:
    """Fast dominant color via kmeans on a downsampled image."""
    try:
        small = cv2.resize(img, (160, 160), interpolation=cv2.INTER_AREA)
        data = small.reshape((-1,3)).astype(np.float32)
        _, labels, centers = cv2.kmeans(data, k, None, (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,10,1.0), 3, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten())
        main = centers[np.argmax(counts)].astype(int)
        return int(main[2]), int(main[1]), int(main[0])  # convert BGR->RGB order
    except Exception:
        h,w = img.shape[:2]
        avg = cv2.resize(img, (1,1)).flatten()
        return int(avg[2]), int(avg[1]), int(avg[0])


def color_histogram_summary(img, bins_h=8, bins_s=3, bins_v=3) -> str:
    """Return a compact coarse HSV histogram summary as a short string."""
    try:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0], None, [bins_h], [0,180]).flatten()
        s = cv2.calcHist([hsv], [1], None, [bins_s], [0,256]).flatten()
        v = cv2.calcHist([hsv], [2], None, [bins_v], [0,256]).flatten()
        # Normalize and quantize to 0-9
        hv = np.concatenate([h, s, v])
        if hv.sum() <= 0:
            return ''
        nv = (hv / hv.sum() * 9).astype(int)
        return ''.join(str(x) for x in nv.tolist())
    except Exception:
        return ''


def estimate_motion_score(frames: List[np.ndarray]) -> float:
    """Estimate motion using mean absolute frame difference normalized to [0,1]."""
    try:
        if len(frames) < 2:
            return 0.0
        prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        totals = []
        for f in frames[1:]:
            g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(prev, g)
            totals.append(float(diff.mean()))
            prev = g
        mean_diff = float(np.mean(totals))
        # Normalize by empirical scaling
        score = min(1.0, mean_diff / 40.0)
        return score
    except Exception:
        return 0.0
