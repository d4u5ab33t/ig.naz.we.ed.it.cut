# example plugin: plugins/vfx_stutter.py

def select_effects(segment_meta):
    energy = segment_meta.get('energy', 0.5)
    shot = segment_meta.get('shot_type', '')
    if shot == 'static' and energy > 0.75:
        return ['stutter']
    return []


def register():
    return {'name': 'vfx_stutter', 'priority': 5, 'select_effects': select_effects}
