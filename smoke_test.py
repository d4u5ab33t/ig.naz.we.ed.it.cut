#!/usr/bin/env python3
# smoke_test.py - quick smoke test for indexer, cache and plugin wiring
import os
import sys
from pathlib import Path
from pprint import pprint

from clip_indexer import ensure_db, index_clip, reindex_dir
from cache_manager import save_cache, load_cache
from plugin_manager import collect_vfx_suggestions
from db import WeeditDB

TEST_CLIP_DIR = Path('test_clips')
DB_PATH = Path('test_weedit.db')
CACHE_PATH = Path('test_weedit_cache.json')


def run_smoke():
    print('Ensure DB')
    conn = ensure_db(DB_PATH)
    print('Indexing small set (limit 5)')
    reindex_dir(TEST_CLIP_DIR, DB_PATH, force=True) if TEST_CLIP_DIR.exists() else print('No test_clips folder')
    db = WeeditDB(str(DB_PATH))
    clips = db.get_all_clips()
    print('Indexed clips count:', len(clips))
    if clips:
        pprint(clips[:3])
        save_cache(clips[:10], CACHE_PATH)
        print('Saved cache ->', CACHE_PATH)
        cache = load_cache(CACHE_PATH)
        print('Loaded cache entries:', len(cache) if cache else 0)
        # plugin test
        meta = {'emotion':'aggressive','shot_type':clips[0].get('shot_type') if clips else 'action','energy':0.9}
        sugs = collect_vfx_suggestions(meta)
        print('Plugin suggestions:')
        pprint(sugs)
    else:
        print('No clips to test')
    conn.close()

if __name__ == '__main__':
    run_smoke()
