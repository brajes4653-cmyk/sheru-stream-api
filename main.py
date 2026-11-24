from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "SheruStream Full Songs Ready"}

@app.get("/search")
def search(q: str):
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. JioSaavn के ऑफिशियल सर्च और मीडिया API से पूरे (Full) गाने निकालें
    try:
        s_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={requests.utils.quote(q)}"
        s_res = requests.get(s_url, headers=headers, timeout=8).json()
        songs = s_res.get("songs", {}).get("data", [])
        
        for song in songs[:10]:
            song_id = song.get("id")
            if not song_id:
                continue
            # हर गाने का फुल स्ट्रीमिंग लिंक निकालें
            d_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0&_format=json&pids={song_id}"
            d_res = requests.get(d_url, headers=headers, timeout=6).json()
            song_data = d_res.get(song_id, {})
            media_preview = song_data.get("media_preview_url", "")
            
            if media_preview:
                # 96kbps प्रिव्यू URL को फुल 320kbps या 160kbps MP4 ऑडियो में बदलें
                full_audio = media_preview.replace("preview.saavncdn.com", "aac.saavncdn.com").replace("_96_p.mp4", "_160.mp4")
                thumb = song_data.get("image", "").replace("150x150", "500x500")
                results.append({
                    "id": song_id,
                    "title": song_data.get("song", song.get("title")),
                    "channel": song_data.get("primary_artists") or "Full Song",
                    "thumbnail": thumb,
                    "audio_url": full_audio,
                    "media_type": "song"
                })
    except Exception:
        pass

    # 2. YouTube सर्च से वीडियो गाने और मूवीज निकालें
    try:
        yt_html = requests.get(f"https://www.youtube.com/results?search_query={requests.utils.quote(q)}", headers=headers, timeout=8).text
        match = re.search(r"var ytInitialData = ({.*?});", yt_html)
        if match:
            data = json.loads(match.group(1))
            contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
            for c in contents:
                v = c.get("videoRenderer")
                if v and v.get("videoId"):
                    vid_id = v["videoId"]
                    title = v["title"]["runs"][0]["text"]
                    channel = v["ownerText"]["runs"][0]["text"] if v.get("ownerText") else "Video"
                    results.append({
                        "id": vid_id,
                        "title": title,
                        "channel": channel,
                        "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        "audio_url": "",
                        "media_type": "video"
                    })
                if len(results) >= 22:
                    break
    except Exception:
        pass

    return {"results": results}
