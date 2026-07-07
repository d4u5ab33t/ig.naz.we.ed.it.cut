#!/usr/bin/env python3
# beat_sync.py
"""
Modified beat_sync minimal integration: supports --use-shot-matching and plugin VFX assignment.
Keeps original pipeline but queries the new DB for shot-type matching.
"""
from pathlib import Path
import argparse
import random
import subprocess
import sys
import tempfile
import os
import json

from db import WeeditDB
from clip_indexer import ClipIndexer
from plugins import load_plugins, apply_plugins

import numpy as np

DEFAULT_MUSIC_DIR = Path(r"D:/Oidasheim/NFOs/mp3s")
DEFAULT_CLIPS_DIR = Path(r"D:/raw_vidz/grok")


def require_tool(name: str) -> str:
    from shutil import which
    p = which(name)
    if not p:
        raise RuntimeError(f"{name} not found")
    return p


def simple_render_segment(ffmpeg, clip_path, start, dur, out_path, vf=''):
    cmd = [ffmpeg, '-y', '-ss', f'{start:.3f}', '-i', str(clip_path), '-t', f'{dur:.3f}', '-an']
    if vf:
        cmd += ['-vf', vf]
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', str(out_path)]
    subprocess.run(cmd, check=True)


def choose_clip_for_segment(db: WeeditDB, desired_shot: str, rng: random.Random):
    # get candidates of same shot type
    cands = db.find_similar_shot_type(desired_shot, limit=200)
    if not cands:
        cands = db.get_all_clips()
    if not cands:
        raise RuntimeError('No clips in DB')
    return rng.choice(cands)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--music-dir', default=str(DEFAULT_MUSIC_DIR))
    parser.add_argument('--clips-dir', default=str(DEFAULT_CLIPS_DIR))
    parser.add_argument('--music')
    parser.add_argument('--use-shot-matching', action='store_true')
    parser.add_argument('--reindex', action='store_true')
    args = parser.parse_args()

    ffmpeg = require_tool('ffmpeg')
    ffprobe = require_tool('ffprobe')

    db = WeeditDB()
    idx = ClipIndexer()
    if args.reindex:
        print('Reindexing clips...')
        idx.index_all()

    load_plugins()

    rng = random.Random(7)
    # minimal: choose first music file
    mus = args.music if args.music else None
    if not mus:
        tracks = list(Path(args.music_dir).glob('*'))
        tracks = [t for t in tracks if t.suffix.lower() in ('.mp3', '.m4a', '.wav')]
        if not tracks:
            print('No tracks found')
            return
        mus = str(tracks[0])
    music_path = Path(mus)
    # simple beat grid: use duration
    dur = 180.0
    try:
        r = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(music_path)], capture_output=True, text=True, timeout=10)
        dur = float(r.stdout.strip())
    except Exception:
        pass

    # build coarse cut points: every 2s
    cut_points = [round(t,3) for t in np.arange(0, dur, 2.0)]
    if cut_points[-1] != dur:
        cut_points.append(dur)

    segments = []
    for a,b in zip(cut_points, cut_points[1:]):
        segments.append({'start':a,'dur':round(b-a,3),'energy':random.random(),'section':'verse'})

    # plugin pre-processing (adds effects)
    segments = apply_plugins(segments)

    with tempfile.TemporaryDirectory(prefix='weedit_') as workdir:
        seg_paths = []
        for idx_i, seg in enumerate(segments):
            desired_shot = 'standard'
            if args.use_shot_matching or args.use_shot_matching:
                # choose shot type by random heuristic
                desired_shot = rng.choice(['action','standard','wide','portrait','cutaway'])
            clip_meta = choose_clip_for_segment(db, desired_shot, rng)
            out = Path(workdir)/f'seg_{idx_i:04d}.mp4'
            try:
                simple_render_segment(ffmpeg, clip_meta['path'], 0.0, seg['dur'], out, vf='')
                seg_paths.append(str(out))
            except Exception as e:
                print('segment render failed', e)

        # concat
        concat_txt = Path(workdir)/'concat.txt'
        concat_txt.write_text('\n'.join(f"file '{p.replace('\\','/')}'" for p in seg_paths))
        out_final = Path('outputs')
        out_final.mkdir(exist_ok=True)
        ts = int(time.time())
        final = out_final/ f'weedit_{music_path.stem}_{ts}.mp4'
        subprocess.run([ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt), '-i', str(music_path), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(final)])
        print('Wrote', final)

if __name__ == '__main__':
    main()
