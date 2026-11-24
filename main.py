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
    return {"status": "online", "message": "SheruStream Permanent Backend Ready"}

@app.get("/search")
def search(q: str):
    results = []
    
    # 1. ऑफिशियल iTunes API से गाने सर्च करें (कभी बंद नहीं होता, सीधा M4A ऑडियो देता है)
    try:
        itunes_url = f"https://itunes.apple.com/search?term={requests.utils.quote(q)}&media=music&limit=10"
        ir = requests.get(itunes_url, timeout=6).json()
        for item in ir.get("results", []):
            if item.get("previewUrl"):
                results.append({
                    "id": str(item.get("trackId")),
                    "title": f"{item.get('trackName')} - {item.get('artistName')}",
                    "channel": item.get("collectionName") or "Music",
                    "thumbnail": item.get("artworkUrl100", "").replace("100x100", "400x400"),
                    "audio_url": item.get("previewUrl"),
                    "media_type": "song"
                })
    except Exception:
        pass

    # 2. सीधे YouTube सर्च से सभी गाने और मूवीज निकालें (बिना किसी थर्ड-पार्टी API के)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
                    channel = v.get("ownerText", {}).get("runs", [{}])[0].get("text", "Video")
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
