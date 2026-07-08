#!/usr/bin/env python3
# cache_manager.py - simple JSON cache read/write for clip metadata
from pathlib import Path
import json
from typing import List, Dict, Any


def save_cache(clips: List[Dict[str, Any]], path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        json.dump(clips, f, indent=2)


def load_cache(path: str):
    p = Path(path)
    if not p.exists():
        return None
    try:
        with p.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None
