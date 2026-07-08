# plugins/plugin_subtitles.py
class Plugin:
    def process(self, timeline, ctx):
        # Example: attach optional subtitles metadata if ctx contains lyrics
        lyrics = ctx.get('lyrics') if ctx else None
        if not lyrics:
            return timeline
        # naive mapping: add first line as subtitle to first segment
        first = timeline[0] if timeline else None
        if first:
            first.setdefault('meta', {})
            first['meta']['subtitle'] = lyrics.splitlines()[0][:120]
        return timeline
