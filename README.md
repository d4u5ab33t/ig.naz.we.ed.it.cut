# README changes: short usage examples & changelog (append)

## Phase 3 additions (short)

New commands:

- Start the watcher (automatically re-index clips when the folder changes):

```bash
python watcher.py --clips "D:/raw_vidz/grok" --db "D:/Oidasheim/weedit/weedit_v4.db"
```

- Index clips on demand:

```bash
python clip_indexer.py --clips "D:/raw_vidz/grok" --db "D:/Oidasheim/weedit/weedit_v4.db" --reindex
```

- Render a single MP3 using shot-matching heuristics (use DB indexed values):

```bash
python beat_sync.py --music "song.mp3" --use-shot-matching
```

Changelog:
- Add quick scene fingerprinting (dhash) and HSV color histograms
- Add shot_type detection (action/static) and persist to DB
- Add plugins/ for VFX selection and two example plugins
- Add watcher daemon (watcher.py) that triggers reindexing on FS changes
- Add hardware_probe.py for platform-aware defaults

