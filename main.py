 from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "SheruStream Unblocked Backend Ready"}

@app.get("/search")
def search(q: str):
    results = []
    # 1. गाने (Songs) सर्च करें - कभी ब्लॉक नहीं होता
    try:
        song_res = requests.get(
            f"https://saavn.dev/api/search/songs?query={requests.utils.quote(q)}&limit=15",
            timeout=8
        ).json()
        for item in song_res.get("data", {}).get("results", []):
            dl = item.get("downloadUrl", [])
            imgs = item.get("image", [])
            if dl:
                results.append({
                    "id": item.get("id"),
                    "title": item.get("name"),
                    "channel": item.get("primaryArtists") or "Music",
                    "thumbnail": imgs[-1]["url"] if imgs else "",
                    "audio_url": dl[-1]["url"],
                    "media_type": "song"
                })
    except Exception:
        pass

    # 2. मूवीज और वीडियो सर्च करें (Public Piped/Invidious API से)
    try:
        vid_res = requests.get(
            f"https://pipedapi.kavin.rocks/search?q={requests.utils.quote(q)}&filter=videos",
            timeout=8
        ).json()
        for v in vid_res.get("items", [])[:10]:
            vid_id = v.get("url", "").replace("/watch?v=", "")
            if vid_id:
                results.append({
                    "id": vid_id,
                    "title": v.get("title"),
                    "channel": v.get("uploaderName") or "Video",
                    "thumbnail": v.get("thumbnail"),
                    "audio_url": "",
                    "media_type": "video"
                })
    except Exception:
        pass

    return {"results": results}

@app.get("/video-stream")
def video_stream(id: str):
    mirrors = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.adminforge.de",
        "https://api.piped.projectsegfau.lt"
    ]
    for base in mirrors:
        try:
            r = requests.get(f"{base}/streams/{id}", timeout=6).json()
            streams = r.get("videoStreams", [])
            audio_streams = r.get("audioStreams", [])
            # ऐसा mp4 चुनें जिसमें ऑडियो+वीडियो साथ हो
            mp4 = [s for s in streams if s.get("format") == "MPEG_4" and not s.get("videoOnly")]
            if mp4:
                return {"video_url": mp4[0]["url"], "audio_url": audio_streams[0]["url"] if audio_streams else ""}
        except Exception:
            continue
    raise HTTPException(status_code=404, detail="Video stream unavailable")
