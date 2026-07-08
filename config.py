# config.py
"""
Project configuration and default paths (local-first)
"""
from pathlib import Path
import os

# Clip pools (checked in order: local-first)
DEFAULT_CLIP_POOLS = [
    r"D:/raw_vidz/grok/_16ZU9",
    r"D:/raw_vidz/grok/_new___",
    r"D:/raw_vidz/grok/9zu16",
    r"D:/raw_vidz/grok/1zu1",
    r"D:/raw_vidz/grok",
]

# Music and output
DEFAULT_MUSIC_DIRS = [
    r"/media/WTF/NFOs/mp3s",
    r"/ubu/WTF/NFOs/mp3s",
    r"\\ubu\\WTF\\NFOs\\mp3s",
    r"D:/Oidasheim/NFOs/mp3s",
]
OUTPUT_DONE_DIR = r"D:/Oidasheim/NFOs/done"

# DB and cache
PREFERRED_DB_SEED = r"I:/Oidasheim/weed_it_dog_pipe-v3.1-Clip.db"
DEFAULT_DB = r"D:/Oidasheim/weedit/weedit_v4.db"
CLIP_CACHE_JSON = r"D:/Oidasheim/weedit/weedit_clip_cache.json"

# FAVs HTML source and destination
FAVS_SOURCE_GLOB = r"D:/Oidasheim/weedit/FAVs*.html"
FAVS_DEST = r"./data/FAVS.html"

# Master brain HTML
MASTER_TMP_HTML = r"D:/Oidasheim/weedit/tmp.html"

# Auto-run behavior (when mp3s present, process into music videos)
AUTO_RUN_MUSIC_DIR = r"D:/Oidasheim/NFOs/mp3s"
AUTO_RUN_POLL_INTERVAL = 10  # seconds

# Annoy index prefix
ANNOY_INDEX_PREFIX = r"D:/Oidasheim/weedit/weedit_color_index"

# Safety
OVERWRITE_OUTPUTS = False  # never overwrite final outputs; use versioned filenames

# Helper: ensure directories exist
def ensure_dirs():
    Path(OUTPUT_DONE_DIR).mkdir(parents=True, exist_ok=True)
    Path(Path(FAVS_DEST).parent).mkdir(parents=True, exist_ok=True)
    Path(Path(DEFAULT_DB).parent).mkdir(parents=True, exist_ok=True)

# Resolve music dirs list: prefer local ones that exist
def resolve_music_dirs():
    existing = [d for d in DEFAULT_MUSIC_DIRS if Path(d).exists()]
    if not existing:
        # fallback to autoplay directory
        return [AUTO_RUN_MUSIC_DIR]
    return existing
