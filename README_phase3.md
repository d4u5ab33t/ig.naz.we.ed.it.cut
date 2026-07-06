# README.md

# WE.ED.IT — Phase 3 (weedit-claw-phase3)

This branch adds Phase‑3 features: fast scene fingerprints, shot‑type detection, color histograms, a plugin system and a background watcher/indexer that keeps the SQLite index up-to-date.

Quickstart:

- Start background watcher (updates DB when new clips appear):

    python watcher.py

- Force reindex all pools immediately:

    python clip_indexer.py

- Render a single MP3 (example entrypoint will be added in next steps):

    python weedit_claw_phase3.py --music "song.mp3" --use-shot-matching

Defaults (local-first paths):

- Clip pools (checked in order):
  - D:\\raw_vidz\\grok
  - /media/Stuff/raw_vidz/grok
  - ubu/Stuff/raw_vidz/grok
  - \\ubu\\Stuff\\raw_vidz\\grok

- Music sources:
  - /media/WTF/NFOs/mp3s
  - /ubu/WTF/NFOs/mp3s
  - \\ubu\\WTF\\NFOs\\mp3s
  - D:\\Oidasheim\\NFOs\\mp3s (sound todo)

DB and cache:

- D:\\Oidasheim\\weedit\\weedit_v4.db
- D:\\Oidasheim\\weedit\\weedit_clip_cache.json

If no DB exists the indexer will copy provided default.clip.db into place if available.

Plugins:

- plugins/plugin_colorgrade.py — mild colorgrade example
- plugins/plugin_subtitles.py — simple subtitles metadata example

Notes:

- This commit is a first-phase integration. It intentionally avoids heavy ML deps (torch) and uses fast approximate algorithms so it runs on low-end devices.

Changelog (Phase‑3):

- add: watcher.py, clip_indexer.py, scene_fingerprint.py
- add: plugins loader + two example plugins
- add: hardware detection helper
- add: weedit_claw_phase3.py entrypoint
- small DB compatibility functions added to db.py

