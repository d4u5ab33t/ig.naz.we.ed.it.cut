# README.md (phase3 additions)

# WE.ED.IT — Phase 3 (weedit-claw-phase3)

This branch adds:

- fast clip indexer (clip_indexer.py) that computes:
  - color histogram
  - motion score (optical flow)
  - shot_type heuristic
  - compact fingerprint
- background watcher (watcher.py) that triggers reindex on new clips
- scene_fingerprint helper (scene_fingerprint.py)
- plugin system under plugins/ with two example plugins
- DB schema extended (db.py) to store fingerprint, hist, shot_type, motion
- beat_sync.py minimal integration demonstrating --reindex and --use-shot-matching

Quick usage:

1) Start the watcher (background):

    python watcher.py D:/raw_vidz/grok

2) Reindex all clips (index now stored in SQLite):

    python clip_indexer.py --reindex

3) Render a single MP3 using shot matching and plugins:

    python beat_sync.py --music "song.mp3" --use-shot-matching

Notes:
- Defaults are local-first (see clip_pools.py). The indexer will resolve pools and scan existing paths.
- No external paid APIs; no torch/transformers required.

Changelog (phase3):
- Add phase 3 clip indexer, watcher, fingerprinting, plugins
- Extend DB schema and add fast approximate fingerprints

