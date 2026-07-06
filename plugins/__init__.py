# plugins/__init__.py
"""Simple plugin loader for weedit plugins.
Plugins must expose a `Plugin` class with a `process(timeline, ctx)` method.
"""
from pathlib import Path
import importlib.util
import sys

PLUGINS_DIR = Path(__file__).parent


def load_plugins(directory: Path = None):
    directory = directory or PLUGINS_DIR
    plugins = []
    for p in directory.glob('plugin_*.py'):
        spec = importlib.util.spec_from_file_location(p.stem, str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[p.stem] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, 'Plugin'):
                plugins.append(mod.Plugin())
        except Exception as e:
            print(f"Failed to load plugin {p}: {e}")
    return plugins
