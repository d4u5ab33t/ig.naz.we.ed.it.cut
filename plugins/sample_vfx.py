#!/usr/bin/env python3
# plugins/sample_vfx.py
"""Example plugin: returns FFmpeg filter strings or metadata for selection.
Plugins must expose `name`, and `match_segment(segment_meta) -> dict`
"""

name = 'sample_vfx'


def match_segment(segment_meta: dict) -> dict:
    """Called by plugin manager with segment metadata (emotion, shot_type, energy).
Return dict with keys: vfx (str), priority (float 0-1), reason (str)
"""
    emotion = segment_meta.get('emotion', 'neutral')
    shot = segment_meta.get('shot_type', 'steady')
    energy = segment_meta.get('energy', 0.5)

    # Simple heuristic: energetic + action -> strobe-like flash (fast brightness eq)
    if emotion in ('aggressive', 'intense') or shot in ('action','dynamic'):
        vfx = "eq=brightness=0.06:saturation=1.2,unsharp=5:5:0.8"
        return {'vfx': vfx, 'priority': 0.8, 'reason': 'energy/action match'}

    if emotion in ('tender','cinematic') or shot in ('steady','dark'):
        vfx = "eq=contrast=1.07:saturation=0.9,format=yuv420p"
        return {'vfx': vfx, 'priority': 0.6, 'reason': 'soft match'}

    # default
    return {'vfx': 'format=yuv420p', 'priority': 0.1, 'reason': 'fallback'}
