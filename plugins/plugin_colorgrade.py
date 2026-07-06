# plugins/plugin_colorgrade.py
class Plugin:
    def process(self, timeline, ctx):
        # Add a mild colorgrade preset to each timeline entry if missing
        for item in timeline:
            item.setdefault('effects', [])
            if 'colorgrade' not in item['effects']:
                item['effects'].append('colorgrade_mild')
        return timeline
