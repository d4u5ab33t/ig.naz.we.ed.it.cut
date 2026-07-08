#!/usr/bin/env python3
# plugin wiring into render loop: update beat_sync to apply top-priority plugin vfx
from pathlib import Path
import argparse
import random
import subprocess
import tempfile
import os
import json
import sys

from db import WeeditDB
from plugin_manager import collect_vfx_suggestions

import numpy as np

DEFAULT_MUSIC_DIR = Path(r"D:/Oidasheim/NFOs/mp3s")
DEFAULT_OUTPUT_DIR = Path(r"D:/Oidasheim/NFOs/done")


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
    cands = db.find_similar_shot_type(desired_shot, limit=200)
    if not cands:
        cands = db.get_all_clips()
    if not cands:
        raise RuntimeError('No clips in DB')
    return rng.choice(cands)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--music')
    parser.add_argument('--use-shot-matching', action='store_true')
    parser.add_argument('--reindex', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    ffmpeg = require_tool('ffmpeg')
    ffprobe = require_tool('ffprobe')

    db = WeeditDB()

    rng = random.Random(7)
    # pick music
    mus = args.music if args.music else None
    if not mus:
        tracks = list(Path(DEFAULT_MUSIC_DIR).glob('*'))
        tracks = [t for t in tracks if t.suffix.lower() in ('.mp3', '.m4a', '.wav')]
        if not tracks:
            print('No tracks found')
            return
        mus = str(tracks[0])
    music_path = Path(mus)
    # get duration
    dur = 180.0
    try:
        r = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(music_path)], capture_output=True, text=True, timeout=10)
        dur = float(r.stdout.strip())
    except Exception:
        pass

    cut_points = [round(t,3) for t in np.arange(0, dur, 3.0)]
    if cut_points[-1] != dur:
        cut_points.append(dur)

    segments = []
    for a,b in zip(cut_points, cut_points[1:]):
        segments.append({'start':a,'dur':round(b-a,3),'energy':random.random(),'section':'verse','shot_type':None})

    with tempfile.TemporaryDirectory(prefix='weedit_') as workdir:
        seg_paths = []
        for idx_i, seg in enumerate(segments[:8]):
            desired_shot = seg.get('shot_type') or rng.choice(['action','steady','dynamic','bright'])
            clip_meta = choose_clip_for_segment(db, desired_shot, rng)
            # collect plugin suggestions
            vfx_sugs = collect_vfx_suggestions({'emotion':'neutral','shot_type':clip_meta.get('shot_type'),'energy':seg.get('energy')})
            vf = ''
            if vfx_sugs:
                top = vfx_sugs[0]
                vf = top.get('vfx','')
                print(f"Segment {idx_i}: applying vfx from plugin {top.get('_plugin')} reason={top.get('reason')}")
            out = Path(workdir)/f'seg_{idx_i:04d}.mp4'
            if args.dry_run:
                print('dry-run: would render', clip_meta['path'], '->', out, 'vf=', vf)
                seg_paths.append(str(out))
                continue
            try:
                simple_render_segment(ffmpeg, clip_meta['path'], 0.0, seg['dur'], out, vf=vf)
                seg_paths.append(str(out))
                db.bump_usage(clip_meta['path'])
            except Exception as e:
                print('segment render failed', e)

        # concat
        if not seg_paths:
            print('no segments produced')
            return
        concat_txt = Path(workdir)/'concat.txt'
        concat_txt.write_text('\n'.join(f"file '{p.replace('\\','/')}'" for p in seg_paths))
        out_final_dir = Path(DEFAULT_OUTPUT_DIR)
        out_final_dir.mkdir(parents=True, exist_ok=True)
        final = out_final_dir / f'weedit_{Path(music_path).stem}_{int(time.time())}.mp4'
        subprocess.run([ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt), '-i', str(music_path), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', str(final)])
        print('Wrote', final)

if __name__ == '__main__':
    main()
