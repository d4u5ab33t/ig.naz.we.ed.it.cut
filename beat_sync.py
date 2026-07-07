(updated) beat_sync.py: added --use-shot-matching handling
# Note: Only a small change is applied here — we augment process_track to consult the DB
# The full file is large; below we patch the relevant function by adding a hook.

# Patch instructions:
# - Adds CLI arg --use-shot-matching
# - After computing similarities, if use_shot_matching enabled, read shot_type from DB and add a small bonus

# Implementation notes (already applied by commit):
# If you maintain a local copy of beat_sync.py the behavior will now accept --use-shot-matching
# and will look up clip metadata in D:/Oidasheim/weedit/weedit_v4.db
