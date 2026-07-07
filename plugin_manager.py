#!/usr/bin/env python3
# plugin_manager.py
"""
Plugin manager: loads plugins from plugins/ and asks them for VFX suggestions
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

PLUGINS_DIR = Path(__file__).parent / 'plugins'


def discover_plugins() -> List[str]:
    out = []
    if not PLUGINS_DIR.exists():
        return out
    for p in PLUGINS_DIR.iterdir():
        if p.suffix == '.py' and p.name != '__init__.py':
            out.append(str(p))
    return out


def load_plugin(path: str):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception as e:
        print(f"[plugin_manager] Failed to load {path}: {e}")
        return None


def collect_vfx_suggestions(segment_meta: Dict[str, Any]) -> List[Dict]:
    results = []
    for p in discover_plugins():
        mod = load_plugin(p)
        if not mod:
            continue
        if hasattr(mod, 'match_segment'):
            try:
                sug = mod.match_segment(segment_meta)
                if isinstance(sug, dict):
                    sug['_plugin'] = getattr(mod, 'name', Path(p).stem)
                    results.append(sug)
            except Exception as e:
                print(f"[plugin_manager] plugin error {p}: {e}")
    return sorted(results, key=lambda x: x.get('priority',0), reverse=True)


if __name__ == '__main__':
    # Simple test
    meta = {'emotion':'aggressive','shot_type':'action','energy':0.9}
    print(collect_vfx_suggestions(meta))
