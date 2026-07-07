# example plugin: plugins/vfx_wobble.py

def select_effects(segment_meta):
    # segment_meta contains keys like 'shot_type', 'energy', 'hist'
    shot = segment_meta.get('shot_type', '')
    energy = segment_meta.get('energy', 0.5)
    if shot == 'action' and energy > 0.6:
        return ['wobble_zoom']
    return []


def register():
    return {'name': 'vfx_wobble', 'priority': 10, 'select_effects': select_effects}
