# plugins/beatdrop.py
"""
Example plugin: injects a brief flash effect on high-energy beats.
"""
class Plugin:
    def process(self, timeline: list) -> list:
        for item in timeline:
            # expect item dict with 'energy' and 'effects' keys
            if item.get('energy', 0) > 0.8:
                item.setdefault('effects', [])
                if 'flash_white' not in item['effects']:
                    item['effects'].append('flash_white')
        return timeline
