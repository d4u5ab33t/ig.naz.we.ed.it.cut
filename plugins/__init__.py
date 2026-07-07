#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple plugin system for VFX/effect selection.
Plugins placed in plugins/ must expose a `register()` function that returns a dict with
'filters' and optional 'priority'. The loader collects available plugins and calls
`select_effects(segment_meta)` on each plugin to allow it to suggest effects.
"""
from __future__ import annotations
import importlib.util
import pkgutil
from pathlib import Path
from typing import List, Dict, Any

PLUGINS_DIR = Path(__file__).parent / 'plugins'


class PluginManager:
    def __init__(self, plugins_dir: Path = PLUGINS_DIR):
        self.plugins_dir = plugins_dir
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        self.plugins = []
        if not self.plugins_dir.exists():
            return
        for finder, name, ispkg in pkgutil.iter_modules([str(self.plugins_dir)]):
            try:
                spec = importlib.util.spec_from_file_location(name, self.plugins_dir / f"{name}.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'register'):
                    self.plugins.append(mod.register())
            except Exception as e:
                print(f"Failed to load plugin {name}: {e}")

    def select_effects(self, segment_meta: Dict[str, Any]) -> List[str]:
        effects = []
        for p in sorted(self.plugins, key=lambda x: x.get('priority', 0), reverse=True):
            try:
                fn = p.get('select_effects')
                if callable(fn):
                    res = fn(segment_meta)
                    if res:
                        effects.extend(res)
            except Exception as e:
                print(f"Plugin error: {e}")
        return effects


# convenience
_default_manager = None

def get_plugin_manager():
    global _default_manager
    if _default_manager is None:
        _default_manager = PluginManager()
    return _default_manager


if __name__ == '__main__':
    pm = PluginManager()
    print(f"Loaded {len(pm.plugins)} plugins")
