import syncedlyrics
import re

class LyricsFetcher:
    def __init__(self):
        self.current_query = ""
        self.lyrics_cache = {}

    def get_lyrics(self, artist, title, provider=None):
        query = f"{title} {artist}"
        if query == self.current_query and query in self.lyrics_cache:
            return self.lyrics_cache[query]
        
        print(f"Fetching lyrics for: {query} (Provider: {provider})")
        
        providers = None
        if provider and provider != "Auto":
            providers = [provider]
            
        try:
            if providers:
                lrc_str = syncedlyrics.search(query, providers=providers)
            else:
                lrc_str = syncedlyrics.search(query)
        except Exception as e:
            print(f"Error fetching from provider {providers}: {e}")
            lrc_str = None
        
        if lrc_str:
            self.current_query = query
            self.lyrics_cache[query] = self.parse_lrc(lrc_str)
            return self.lyrics_cache[query]
        return None

    def parse_lrc(self, lrc_str):
        if not lrc_str:
            return []
        
        lines = []
        # Regex for [mm:ss.xx] or [mm:ss.xxx]
        pattern = re.compile(r'\[(\d+):(\d+(?:\.\d+)?)\](.*)')
        
        for line in lrc_str.splitlines():
            match = pattern.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                text = match.group(3).strip()
                total_seconds = minutes * 60 + seconds
                if text: # Skip empty lines? Or keep them to clear text?
                    lines.append((total_seconds, text))
        
        # Sort by time just in case
        lines.sort(key=lambda x: x[0])
        return lines

if __name__ == "__main__":
    fetcher = LyricsFetcher()
    # Test with a known song
    lyrics = fetcher.get_lyrics("Rick Astley", "Never Gonna Give You Up")
    if lyrics:
        for t, text in lyrics[:5]:
            print(f"{t}: {text}")
