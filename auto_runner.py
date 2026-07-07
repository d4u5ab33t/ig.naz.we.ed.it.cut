#!/usr/bin/env python3
"""
auto_runner.py
Watch the music directory and, when MP3 files appear, trigger the beat_sync renderer
for each unprocessed MP3. Moves processed MP3s to the done folder to avoid reprocessing.
"""
import time
import subprocess
from pathlib import Path
import shutil
import os
from config import AUTO_RUN_MUSIC_DIR, AUTO_RUN_POLL_INTERVAL, OUTPUT_DONE_DIR

BEAT_SYNC_SCRIPT = 'beat_sync.py'


def process_new_mp3(mp3_path: Path):
    print(f"[auto_runner] processing: {mp3_path}")
    try:
        subprocess.run(['python', BEAT_SYNC_SCRIPT, '--music', str(mp3_path)], check=True)
        # move to done folder
        dest = Path(OUTPUT_DONE_DIR) / mp3_path.name
        dest = _unique_path(dest)
        shutil.move(str(mp3_path), str(dest))
        print(f"[auto_runner] moved processed track to {dest}")
    except Exception as e:
        print(f"[auto_runner] failed to process {mp3_path}: {e}")


def _unique_path(p: Path) -> Path:
    if not p.exists():
        return p
    stem = p.stem
    suffix = p.suffix
    i = 1
    while True:
        candidate = p.parent / f"{stem}_v{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main():
    music_dir = Path(AUTO_RUN_MUSIC_DIR)
    if not music_dir.exists():
        print(f"[auto_runner] music dir {music_dir} does not exist")
        return
    seen = set()
    while True:
        mp3s = list(music_dir.glob('*.mp3'))
        for m in mp3s:
            if str(m) in seen:
                continue
            process_new_mp3(m)
            seen.add(str(m))
        time.sleep(AUTO_RUN_POLL_INTERVAL)

if __name__ == '__main__':
    main()
