from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

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
    return {"status": "online", "message": "Kipit API is running!"}

@app.post("/api/download")
def get_video_link(request: VideoRequest):
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            # Agar multiple entries / carousel post ho
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            video_url = info.get('url')
            title = info.get('title', 'Kipit Video')
            thumbnail = info.get('thumbnail', '')

            # Formats me direct MP4 search karein
            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('ext') == 'mp4' or 'mp4' in f.get('format', '')):
                        video_url = f.get('url')
                        break

            if not video_url:
                raise HTTPException(status_code=400, detail="Video stream extract nahi ho paayi.")

            return {
                "status": "success",
                "download_url": video_url,
                "title": title,
                "thumbnail": thumbnail
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
