#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watcher.py
Watches configured clip directories and triggers the clip_indexer on file system changes.
Requires watchdog package.
"""
from __future__ import annotations
import time
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEFAULT_CLIPS = [
    r"D:/raw_vidz/grok",
    r"/media/Stuff/raw_vidz/grok",
    r"/ubu/Stuff/raw_vidz/grok",
    r"\\ubu\\Stuff\\raw_vidz\\grok",
]
DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"


class _ReindexHandler(FileSystemEventHandler):
    def __init__(self, clips_dir: str, db_path: str):
        self.clips_dir = clips_dir
        self.db_path = db_path
        self._last = 0

    def on_any_event(self, event):
        # debounce rapid events
        now = time.time()
        if now - self._last < 2.0:
            return
        self._last = now
        print(f"Change detected: {event.src_path}. Triggering indexer...")
        try:
            subprocess.Popen([sys.executable, 'clip_indexer.py', '--clips', self.clips_dir, '--db', self.db_path])
        except Exception as e:
            print(f"Failed to spawn indexer: {e}")


def start_watcher(clips_dir: str = None, db_path: str = DEFAULT_DB):
    clips_dir = clips_dir or DEFAULT_CLIPS[0]
    handler = _ReindexHandler(clips_dir, db_path)
    obs = Observer()
    obs.schedule(handler, clips_dir, recursive=True)
    obs.start()
    print(f"Watching {clips_dir} for changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--clips', default=None)
    parser.add_argument('--db', default=DEFAULT_DB)
    args = parser.parse_args()
    start_watcher(args.clips, args.db)
