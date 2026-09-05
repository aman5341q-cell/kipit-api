from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import urllib.request
import urllib.parse
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"status": "online", "message": "Kipit Universal Multi-Platform Engine is running!"}

# ⚡ Turbo Configuration for Fast Extraction
TURBO_YDL_OPTS = {
    'format': 'best[ext=mp4]/best',
    'skip_download': True,
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'playlist_items': '1',
    'check_formats': False,
    'cachedir': False,
    'socket_timeout': 12,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

@app.post("/api/download")
def get_video_link(request: VideoRequest):
    target_url = request.url.strip()

    # 🛡️ 1. Zero-Tolerance Policy Check: Block YouTube completely
    lower_url = target_url.lower()
    if "youtube.com" in lower_url or "youtu.be" in lower_url:
        raise HTTPException(
            status_code=400, 
            detail="YouTube downloading is strictly not supported as per developer policies."
        )

    # ⚡ 2. Instant 300ms Fast-Path for TikTok (100% No-Watermark)
    if "tiktok.com" in lower_url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(target_url)}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode())
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    return {
                        "status": "success",
                        "download_url": d.get("play"),
                        "title": d.get("title", "TikTok Video (No Watermark)"),
                        "thumbnail": d.get("cover", "")
                    }
        except Exception:
            pass  # Fallback to general extractor if API busy

    # 🌐 3. Universal Engine for Instagram, Facebook, X, Pinterest, Reddit & 1000+ Platforms
    try:
        with yt_dlp.YoutubeDL(TURBO_YDL_OPTS) as ydl:
            info = ydl.extract_info(target_url, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            video_url = info.get('url')
            title = info.get('title', 'Social Media Video')
            thumbnail = info.get('thumbnail', '')

            # Extract best MP4 stream
            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('ext') == 'mp4' or 'mp4' in f.get('format', '')):
                        video_url = f.get('url')
                        break

            if not video_url:
                raise HTTPException(status_code=400, detail="Video stream extract nahi ho paayi. Link public hai check karein.")

            return {
                "status": "success",
                "download_url": video_url,
                "title": title,
                "thumbnail": thumbnail
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
