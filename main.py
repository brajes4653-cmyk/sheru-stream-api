from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "New SheruStream Backend Ready"}

@app.get("/search")
def search(q: str, limit: int = 15):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{q}", download=False)
            results = []
            for entry in info.get('entries', []):
                if entry:
                    results.append({
                        "id": entry.get("id"),
                        "title": entry.get("title"),
                        "channel": entry.get("uploader"),
                        "thumbnail": f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg"
                    })
            return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
def stream(id: str, type: str = "audio"):
    url = f"https://www.youtube.com/watch?v={id}"
    fmt = "bestaudio[ext=m4a]/bestaudio" if type == "audio" else "best[ext=mp4][height<=720]/best[ext=mp4]"
    
    ydl_opts = {
        'quiet': True,
        'format': fmt,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "stream_url": info.get("url"),
                "thumbnail": info.get("thumbnail")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
