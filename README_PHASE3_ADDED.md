Phase‑3 additions: clip indexer, scene fingerprinting, plugin manager, sample plugin, watcher, hardware detection, and DB helper.

Usage examples added:
- python watcher.py --watch D:/raw_vidz/grok --db D:/Oidasheim/weedit/weedit_v4.db
- python clip_indexer.py --dir D:/raw_vidz/grok --db D:/Oidasheim/weedit/weedit_v4.db --reindex
- import plugin_manager and call collect_vfx_suggestions(segment_meta)

Notes:
- These modules are lightweight, avoid heavy ML libs and rely on OpenCV + numpy + watchdog.
- They will not overwrite existing files; they are new additions in branch weedit-claw-phase3.
