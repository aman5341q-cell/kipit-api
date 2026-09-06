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
    return {"status": "online", "message": "Kipit Universal API is running!"}

@app.post("/api/download")
def get_video_link(request: VideoRequest):
    target_url = request.url.strip()

    # ⚡ 1. TikTok Fast-Path (0.3s)
    if "tiktok.com" in target_url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(target_url)}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("code") == 0 and data.get("data"):
                    d = data["data"]
                    return {
                        "status": "success",
                        "download_url": d.get("play"),
                        "title": d.get("title", "TikTok Video"),
                        "thumbnail": d.get("cover", "")
                    }
        except Exception:
            pass

    # 🚀 2. Universal Stream Extractor (Reddit, Instagram, FB, X & others)
    try:
        # Bina strict format restriction ke extract karein taaki format unavailable error na aaye
        opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'playlist_items': '1',
            'check_formats': False,
            'cachedir': False,
            'socket_timeout': 15,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            title = info.get('title', 'Kipit Media')
            thumbnail = info.get('thumbnail', '')
            media_url = info.get('url')

            # Sabse best video stream dhoondhein
            if not media_url and 'formats' in info:
                # 1st priority: Audio aur Video dono ho
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('vcodec') != 'none' and f.get('acodec') != 'none'):
                        media_url = f.get('url')
                        break
                # 2nd priority: Koi bhi valid video stream
                if not media_url:
                    for f in reversed(info['formats']):
                        if f.get('url') and f.get('vcodec') != 'none':
                            media_url = f.get('url')
                            break
                # 3rd priority: Jo bhi direct URL available ho
                if not media_url:
                    for f in reversed(info['formats']):
                        if f.get('url'):
                            media_url = f.get('url')
                            break

            # Agar post me video nahi hai, balki Image/Meme/Photo hai:
            if not media_url and thumbnail:
                media_url = thumbnail

            if not media_url:
                raise HTTPException(status_code=400, detail="Is link me koi video ya media nahi mila.")

            return {
                "status": "success",
                "download_url": media_url,
                "title": title,
                "thumbnail": thumbnail or media_url
            }
    except Exception as e:
        err = str(e)
        if "Requested format is not available" in err:
            err = "Is post me direct video stream available nahi hai."
        raise HTTPException(status_code=400, detail=err)
        
