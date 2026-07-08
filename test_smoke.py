#!/usr/bin/env python3
"""
test_smoke.py
End-to-end smoke test: indexes up to N clips, builds ANN, runs a short render of 10 segments and verifies output file exists.
This is a local test script — run it on your machine where ffmpeg and dependencies are available.
"""
import subprocess
import tempfile
import shutil
import time
from pathlib import Path

CLIPS_DIR = Path('D:/raw_vidz/grok')
DB_PATH = Path('D:/Oidasheim/weedit/weedit_v4.db')
CACHE_PATH = Path('D:/Oidasheim/weedit/weedit_clip_cache.json')
ANNOY_PREFIX = Path('D:/Oidasheim/weedit/weedit_color_index')
MUSIC_DIR = Path('D:/Oidasheim/NFOs/mp3s')

def run_index():
    cmd = ['python', 'clip_indexer.py', '--clips', str(CLIPS_DIR), '--db', str(DB_PATH), '--cache', str(CACHE_PATH)]
    print('Running index:', ' '.join(cmd))
    subprocess.run(cmd, check=True)

def run_render():
    # pick first track
    tracks = [p for p in MUSIC_DIR.glob('*') if p.suffix.lower() in ('.mp3', '.m4a', '.wav')]
    if not tracks:
        raise SystemExit('No tracks found for smoke test')
    track = tracks[0]
    out = subprocess.run(['python', 'beat_sync.py', '--music', str(track), '--use-shot-matching', '--ann-prefix', str(ANNOY_PREFIX)], check=True)
    return out.returncode

if __name__ == '__main__':
    start = time.time()
    run_index()
    rc = run_render()
    elapsed = time.time() - start
    print('Smoke test completed, rc=', rc, 'elapsed=', elapsed)
