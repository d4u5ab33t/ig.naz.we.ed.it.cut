#!/usr/bin/env python3
# watcher.py
"""
Folder watcher daemon: watches clip folders and triggers indexer for new files.
Requires watchdog (pip install watchdog)
Usage:
    python watcher.py --watch D:/raw_vidz/grok --db D:/Oidasheim/weedit/weedit_v4.db
"""
from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print('Please install watchdog: pip install watchdog')
    raise


class ClipEventHandler(FileSystemEventHandler):
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def on_created(self, event):
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.suffix.lower() in ('.mp4','.mov','.mkv','.avi'):
            # call indexer for this file
            from clip_indexer import ensure_db, index_clip
            conn = ensure_db(self.db_path)
            print(f"[watcher] New clip detected: {p.name}")
            index_clip(conn, p, force=True)
            conn.close()


def run_watch(path: Path, db_path: Path):
    event_handler = ClipEventHandler(db_path)
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()
    print(f"Watching {path} ...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', '-w', required=True)
    parser.add_argument('--db', default=r"D:/Oidasheim/weedit/weedit_v4.db")
    args = parser.parse_args()
    run_watch(Path(args.watch), Path(args.db))


if __name__ == '__main__':
    main()
