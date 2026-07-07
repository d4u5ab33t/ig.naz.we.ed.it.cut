#!/usr/bin/env python3
# watcher.py
"""
Simple background folder watcher that triggers clip indexer updates when new files arrive.
Requires watchdog.
"""
import time
from pathlib import Path
import subprocess
import sys

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print('Please install watchdog: pip install watchdog')
    sys.exit(1)

class _EventHandler(FileSystemEventHandler):
    def __init__(self, index_cmd: str):
        super().__init__()
        self.index_cmd = index_cmd
    def on_created(self, event):
        if event.is_directory: return
        print(f"[watcher] file created: {event.src_path}")
        subprocess.Popen(self.index_cmd, shell=True)
    def on_moved(self, event):
        if event.is_directory: return
        print(f"[watcher] file moved: {event.dest_path}")
        subprocess.Popen(self.index_cmd, shell=True)


def main(paths):
    index_cmd = 'python clip_indexer.py --reindex'
    handler = _EventHandler(index_cmd)
    obs = Observer()
    for p in paths:
        print(f"[watcher] watching: {p}")
        obs.schedule(handler, str(p), recursive=True)
    obs.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    args = parser.parse_args()
    watch_paths = args.paths if args.paths else ['D:/raw_vidz/grok']
    main(watch_paths)
