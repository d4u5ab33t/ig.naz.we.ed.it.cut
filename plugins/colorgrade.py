# plugins/colorgrade.py
"""
Example plugin: applies colorgrade metadata for chorus sections.
"""
class Plugin:
    def process(self, timeline: list) -> list:
        for item in timeline:
            if item.get('section') == 'chorus':
                item.setdefault('effects', [])
                if 'color_pop' not in item['effects']:
                    item['effects'].append('color_pop')
        return timeline
