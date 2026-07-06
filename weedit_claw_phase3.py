#!/usr/bin/env python3
"""weedit_claw_phase3.py - new entrypoint integrating Phase3 features
Usage:
  python weedit_claw_phase3.py --music "song.mp3" --use-shot-matching
"""
import argparse
from pathlib import Path
import logging

from clip_indexer import ClipIndexer
from watcher import start_watcher
from plugins import load_plugins
from clip_pools import resolve_pools
from db import WeeditDB

LOG = logging.getLogger('weedit.phase3')
logging.basicConfig(level=logging.INFO)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--music', help='song file or partial name')
    p.add_argument('--use-shot-matching', action='store_true')
    p.add_argument('--start-watcher', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    db = WeeditDB()
    indexer = ClipIndexer()
    plugins = load_plugins()

    if args.start_watcher:
        pools = resolve_pools(verbose=True)
        start_watcher(indexer)
        return

    # ensure index ready
    indexer.scan_pools(force=True)

    # simple demo: list top 10 clips
    clips = db.get_all_clips()
    print(f"Indexed clips: {len(clips)}")
    for c in clips[:10]:
        print(c.get('path'), c.get('shot_type'))

    # show loaded plugins
    print('Loaded plugins:', [type(p).__name__ for p in plugins])

if __name__ == '__main__':
    main()
