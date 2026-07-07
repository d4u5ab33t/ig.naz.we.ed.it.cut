# plugins/__init__.py
"""
Plugin loader for WE.ED.IT. Plugins must define a `Plugin` class with
`process(timeline: list) -> list` method.
"""
from importlib import import_module
from pathlib import Path
import pkgutil

PLUGINS = {}


def load_plugins(pkg='plugins'):
    root = Path(__file__).parent
    for finder, name, ispkg in pkgutil.iter_modules([str(root)]):
        if name.startswith('_'):
            continue
        try:
            m = import_module(f'plugins.{name}')
            if hasattr(m, 'Plugin'):
                PLUGINS[name] = m.Plugin()
        except Exception:
            pass
    return PLUGINS


def apply_plugins(timeline: list) -> list:
    for name, plugin in PLUGINS.items():
        try:
            timeline = plugin.process(timeline)
        except Exception:
            pass
    return timeline
