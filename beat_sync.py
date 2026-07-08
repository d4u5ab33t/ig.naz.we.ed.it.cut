#!/usr/bin/env python3
"""
Updated beat_sync.py: expanded EFFECT_TEMPLATES with parameterized filter templates
and Annoy-backed color continuity selection when available.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import tempfile
import time
import random
import json
import os
from typing import List, Dict, Any, Optional

from db import WeeditDB
from clip_indexer import ClipIndexer
from plugins import get_plugin_manager
from ann_index import AnnIndex

# simple defaults
DEFAULT_MUSIC_DIR = Path(r"D:/Oidasheim/NFOs/mp3s")
DEFAULT_CLIPS_DIR = Path(r"D:/raw_vidz/grok")
OUTPUT_DIR = Path(r"D:/Oidasheim/NFOs/done")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Parameterized templates for common effects. Use .format(**params) to render.
EFFECT_TEMPLATES: Dict[str, str] = {
    'colorgrade_mild': "eq=contrast={contrast}:brightness={brightness}:saturation={saturation}",
    'color_pop': "eq=contrast={contrast}:saturation={saturation}",
    'neon_pulse': "colorbalance=rs={r}:gs={g}:bs={b}",
    'soft_fade': "fade=t=in:st=0:d={d}",
    'clean': "",
    'flash_white': "colorlevels=rimin=0:gimin=0:bimin=0:romax={bright}:gomax={bright}:bomax={bright}",
    'wobble_zoom': "zoompan=z='if(gt(t,{start}),{zoom},1)':d=1",
    'stutter': "tblend=all_mode='average',framestep=2",
    'vignette': "vignette=PI/4:0.5"
}


def build_vf_from_effects(effects: List[Any]) -> str:
    parts = []
    for e in effects:
        # support either string (effect name) or dict {'effect':name,'params':{}}
        name = e if isinstance(e, str) else e.get('effect')
        params = {} if isinstance(e, str) else e.get('params', {})
        tpl = EFFECT_TEMPLATES.get(name)
        if not tpl:
            continue
        try:
            vf = tpl.format(**params)
        except Exception:
            vf = tpl
        if vf:
            parts.append(vf)
    return ",".join(parts)


def require_tool(name: str) -> str:
    from shutil import which
    p = which(name)
    if not p:
        raise RuntimeError(f"{name} not found on PATH")
    return p


def simple_render_segment(ffmpeg, clip_path, start, dur, out_path, vf=''):
    cmd = [ffmpeg, '-y', '-ss', f'{start:.3f}', '-i', str(clip_path), '-t', f'{dur:.3f}', '-an']
    if vf:
        cmd += ['-vf', vf]
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(out_path)]
    subprocess.run(cmd, check=True)


def choose_clip_for_segment(db: WeeditDB, desired_shot: str, rng: random.Random, ann: Optional[AnnIndex] = None, prev_clip_path: Optional[str] = None) -> Dict[str, Any]:
    cands = db.get_all_clips()
    if not cands:
        raise RuntimeError('No clips available in DB')
    # If ANN is available and prev_clip_path provided, query ANN for nearest by color
    if ann and prev_clip_path:
        prev = db.get_clip_metadata(prev_clip_path)
        vec = prev.get('color_histogram') if prev else None
        if vec and isinstance(vec, list):
            try:
                res = ann.query(vec, k=40)
                paths = [r[0] for r in res]
                # convert paths to clip meta
                pool = [c for c in cands if c['path'] in paths]
                if pool:
                    # prefer same shot type if possible
                    same_shot = [c for c in pool if c.get('shot_type') == desired_shot]
                    pool = same_shot if same_shot else pool
                    return rng.choice(pool)
            except Exception:
                pass
    # fallback: prefer same shot
    same = [c for c in cands if c.get('shot_type') == desired_shot]
    pool = same if same else cands
    return rng.choice(pool)


def concat_and_mux(ffmpeg: str, segment_paths: List[str], music_path: Path, output_path: Path, work_dir: Path):
    concat_file = work_dir / 'concat.txt'
    with open(concat_file, 'w', encoding='utf-8') as f:
        for p in segment_paths:
            f.write(f"file '{Path(p).as_posix()}'\n")
    silent_video = work_dir / 'silent_video.mp4'
    subprocess.run([ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'copy', str(silent_video)], check=True)
    subprocess.run([ffmpeg, '-y', '-i', str(silent_video), '-i', str(music_path), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(output_path)], check=True)


def load_ann_index_if_available(prefix: str):
    try:
        return AnnIndex(prefix)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--music-dir', default=str(DEFAULT_MUSIC_DIR))
    parser.add_argument('--clips-dir', default=str(DEFAULT_CLIPS_DIR))
    parser.add_argument('--music')
    parser.add_argument('--use-shot-matching', action='store_true')
    parser.add_argument('--reindex', action='store_true')
    parser.add_argument('--db', default=r'D:/Oidasheim/weedit/weedit_v4.db')
    parser.add_argument('--ann-prefix', default=r'D:/Oidasheim/weedit/weedit_color_index')
    args = parser.parse_args()

    ffmpeg = require_tool('ffmpeg')
    ffprobe = require_tool('ffprobe')

    db = WeeditDB(args.db)
    db._init_db()

    idx = ClipIndexer()
    if args.reindex:
        print('Reindexing...')
        idx.scan_and_index(args.clips_dir, args.db)

    ann = load_ann_index_if_available(args.ann_prefix)

    pm = get_plugin_manager()

    # select music
    if args.music:
        music_path = Path(args.music)
    else:
        tracks = list(Path(args.music_dir).glob('*'))
        tracks = [t for t in tracks if t.suffix.lower() in ('.mp3', '.m4a', '.wav')]
        if not tracks:
            raise SystemExit('No music found')
        music_path = tracks[0]

    # duration probe
    try:
        r = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(music_path)], capture_output=True, text=True, timeout=10)
        duration = float(r.stdout.strip())
    except Exception:
        duration = 120.0

    # build cut grid: simple every 2s
    step = 2.0
    cut_points = [round(t, 3) for t in range(0, int(duration), int(step))]
    if cut_points[-1] != duration:
        cut_points.append(duration)

    segments = []
    rng = random.Random(7)
    for a, b in zip(cut_points, cut_points[1:]):
        seg = {'start': a, 'dur': round(b - a, 3), 'energy': rng.random(), 'section': 'verse'}
        segments.append(seg)

    # for each segment, ask plugins for suggested effects
    for seg in segments:
        try:
            plugin_effects = pm.select_effects(seg)
        except Exception:
            plugin_effects = []
        seg.setdefault('effects', [])
        for ef in plugin_effects:
            if ef not in seg['effects']:
                seg['effects'].append(ef)

    # render segments
    with tempfile.TemporaryDirectory(prefix='weedit_') as td:
        work_dir = Path(td)
        segment_paths = []
        prev_clip = None
        for i, seg in enumerate(segments):
            desired_shot = rng.choice(['standard', 'wide', 'action', 'static', 'cutaway']) if args.use_shot_matching else 'standard'
            clip_meta = choose_clip_for_segment(db, desired_shot, rng, ann=ann, prev_clip_path=prev_clip)
            vf = build_vf_from_effects(seg.get('effects', []))
            out_seg = work_dir / f'seg_{i:04d}.mp4'
            try:
                simple_render_segment(ffmpeg, clip_meta['path'], 0.0, seg['dur'], out_seg, vf=vf)
                segment_paths.append(str(out_seg))
                prev_clip = clip_meta['path']
            except Exception as e:
                print('Failed render segment:', e)

        # mux
        ts = int(time.time())
        output_path = OUTPUT_DIR / f'weedit_{music_path.stem}_{ts}.mp4'
        concat_and_mux(ffmpeg, segment_paths, music_path, output_path, work_dir)
        print('Wrote', output_path)


if __name__ == '__main__':
    main()
