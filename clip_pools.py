# clip_pools.py
"""
Resolve clip pool directories using local-first defaults from config.py
Also helpers for selecting DB paths and copying default DB if missing.
"""
from pathlib import Path
import shutil
import glob
import os
from typing import List, Optional

from config import DEFAULT_CLIP_POOLS, DEFAULT_DB, PREFERRED_DB_SEED, CLIP_CACHE_JSON, FAVS_SOURCE_GLOB, FAVS_DEST


def resolve_pools(tags_filter: List[str] | None = None, verbose: bool = False) -> List[str]:
    out = []
    for p in DEFAULT_CLIP_POOLS:
        if Path(p).exists():
            out.append(p)
            if verbose:
                print(f"[clip_pools] using pool: {p}")
    # if none found, just return the canonical path (may be network mounted later)
    if not out:
        out = DEFAULT_CLIP_POOLS[:]
    return out


def choose_db_path(target_db: str = DEFAULT_DB) -> str:
    """Choose DB path. If target_db doesn't exist, attempt to copy preferred seed.
    If multiple DBs (*.db) exist in current dir, pick the largest.
    """
    t = Path(target_db)
    if t.exists():
        return str(t)
    # try preferred seed
    seed = Path(PREFERRED_DB_SEED)
    if seed.exists():
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(seed), str(t))
            print(f"[clip_pools] Copied seed DB from {seed} to {t}")
            return str(t)
        except Exception as e:
            print(f"[clip_pools] Failed to copy seed DB: {e}")
    # no seed: find largest .db in cwd
    dbs = list(Path('.').glob('*.db')) + list(Path('.').glob('*.sqlite'))
    if dbs:
        dbs_sorted = sorted(dbs, key=lambda p: p.stat().st_size, reverse=True)
        chosen = dbs_sorted[0]
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(chosen), str(t))
            print(f"[clip_pools] Copied largest DB {chosen} to {t}")
            return str(t)
        except Exception as e:
            print(f"[clip_pools] Failed to copy largest DB: {e}")
    # nothing to copy: return target path (will be created by DB initializer)
    return str(t)


def copy_latest_favs(source_glob: str = FAVS_SOURCE_GLOB, dest: str = FAVS_DEST):
    matches = glob.glob(source_glob)
    if not matches:
        return None
    matches_sorted = sorted(matches, key=lambda p: Path(p).stat().st_mtime, reverse=True)
    latest = matches_sorted[0]
    try:
        Path(Path(dest).parent).mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest, dest)
        print(f"[clip_pools] Copied latest FAVs {latest} -> {dest}")
        return dest
    except Exception as e:
        print(f"[clip_pools] Failed to copy FAVs: {e}")
        return None
