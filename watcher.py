#!/usr/bin/env python3
# watcher.py - Background folder watcher to keep clip index up-to-date
import time
import logging
from pathlib import Path
from typing import List

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object

from clip_indexer import ClipIndexer
from clip_pools import resolve_pools

LOG = logging.getLogger("weedit.watcher")

class _IndexEventHandler(FileSystemEventHandler):
    def __init__(self, indexer: ClipIndexer, watched_dirs: List[Path]):
        self.indexer = indexer
        self.watched = set(str(p.resolve()) for p in watched_dirs)

    def on_created(self, event):
        path = getattr(event, 'src_path', None)
        if not path: return
        LOG.info("FS event created: %s", path)
        self.indexer.index_path(path)

    def on_modified(self, event):
        path = getattr(event, 'src_path', None)
        if not path: return
        LOG.debug("FS event modified: %s", path)
        self.indexer.index_path(path)

    def on_moved(self, event):
        path = getattr(event, 'dest_path', None)
        if not path: return
        LOG.info("FS event moved: %s", path)
        self.indexer.index_path(path)


def start_watcher(indexer: ClipIndexer, pool_tags: List[str] | None = None, poll_interval: float = 1.0):
    """Start a background watcher that observes resolved clip pools and calls the indexer."""
    dirs = resolve_pools(tags_filter=pool_tags, verbose=False)
    watch_dirs = [Path(d) for d in dirs]

    if Observer is None:
        LOG.warning("watchdog not installed — falling back to periodic rescan (poll every %ss)", poll_interval)
        try:
            while True:
                indexer.reindex_if_needed()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            LOG.info("Watcher stopped")
        return

    obs = Observer()
    handler = _IndexEventHandler(indexer, watch_dirs)
    for d in watch_dirs:
        LOG.info("Watching %s", d)
        obs.schedule(handler, str(d), recursive=True)
    obs.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        LOG.info("Stopping watcher...")
        obs.stop()
    obs.join()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    idx = ClipIndexer()
    start_watcher(idx)
