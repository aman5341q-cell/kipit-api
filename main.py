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
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            video_url = info.get('url')
            title = info.get('title', 'Kipit Video')
            thumbnail = info.get('thumbnail', '')

            if not video_url and 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('ext') == 'mp4' and f.get('url'):
                        video_url = f.get('url')
                        break

            if not video_url:
                raise HTTPException(status_code=400, detail="Video link nahi mil paya")

            return {
                "status": "success",
                "download_url": video_url,
                "title": title,
                "thumbnail": thumbnail
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
