import yt_dlp
import pandas as pd

search_term = "mukbang"
max_results = 20  # Increase later!

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'noplaylist': True,
}

search_url = f"ytsearch{max_results}:{search_term}"

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    result = ydl.extract_info(search_url, download=False)

videos = result.get('entries', [])
df = pd.DataFrame(videos)
df.to_csv("data/mukbang_metadata.csv", index=False)
print(df.columns.tolist())  # Show all available fields
print(df.head())            # Preview the actual data
