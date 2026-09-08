from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
import urllib.parse
import json
import re
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
    return {"status": "online", "message": "Kipit Ultra Fast Engine is active!"}

# 🚀 Layer 1: Super-Fast Direct Extractors (< 1 Second)
def fast_extract_instagram(url: str):
    match = re.search(r'instagram\.com/(?:reel|p|reels)/([A-Za-z0-9_-]+)', url)
    if not match:
        return None
    shortcode = match.group(1)
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    req = urllib.request.Request(embed_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read().decode('utf-8', errors='ignore')
            v_match = re.search(r'"video_url"\s*:\s*"([^"]+)"', html)
            if v_match:
                clean_url = v_match.group(1).encode('utf-8').decode('unicode_escape').replace('\\/', '/')
                return clean_url
    except Exception:
        pass
    return None

def fast_extract_facebook(url: str):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            m = re.search(r'["\']browser_native_hd_url["\']\s*:\s*["\']([^"\']+)["\']', html) or \
                re.search(r'hd_src["\']?\s*:\s*["\']([^"\']+)["\']', html) or \
                re.search(r'["\']browser_native_sd_url["\']\s*:\s*["\']([^"\']+)["\']', html) or \
                re.search(r'sd_src["\']?\s*:\s*["\']([^"\']+)["\']', html)
            if m:
                clean_url = m.group(1).encode('utf-8').decode('unicode_escape').replace('\\/', '/')
                return clean_url
    except Exception:
        pass
    return None

def fast_extract_tiktok(url: str):
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            if data.get("code") == 0 and data.get("data"):
                d = data["data"]
                return d.get("play"), d.get("title", "TikTok Video"), d.get("cover", "")
    except Exception:
        pass
    return None, None, None

# ⚡ Layer 2: Fast yt-dlp Settings
TURBO_YDL_OPTS = {
    'format': 'best[ext=mp4]/best',
    'skip_download': True,
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'playlist_items': '1',
    'check_formats': False,
    'cachedir': False,
    'socket_timeout': 8,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

@app.post("/api/download")
def get_video_link(request: VideoRequest):
    target_url = request.url.strip()

    # 1. TikTok Instant Path (0.3s)
    if "tiktok.com" in target_url:
        t_url, title, thumb = fast_extract_tiktok(target_url)
        if t_url:
            return {"status": "success", "download_url": t_url, "title": title, "thumbnail": thumb}

    # 2. Instagram Instant Path (< 1s)
    if "instagram.com" in target_url:
        insta_url = fast_extract_instagram(target_url)
        if insta_url:
            return {"status": "success", "download_url": insta_url, "title": "Instagram Video", "thumbnail": ""}

    # 3. Facebook Instant Path (< 1.2s)
    if "facebook.com" in target_url or "fb.watch" in target_url:
        fb_url = fast_extract_facebook(target_url)
        if fb_url:
            return {"status": "success", "download_url": fb_url, "title": "Facebook Video", "thumbnail": ""}

    # 4. Fallback to Optimized yt-dlp
    try:
        with yt_dlp.YoutubeDL(TURBO_YDL_OPTS) as ydl:
            info = ydl.extract_info(target_url, download=False)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            video_url = info.get('url')
            title = info.get('title', 'Kipit Video')
            thumbnail = info.get('thumbnail', '')

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
        
