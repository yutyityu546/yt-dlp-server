from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Разрешаем запросы с любого плеера / сайта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/stream")
def get_stream(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if not audio_url:
                raise HTTPException(status_code=404, detail="Stream URL not found")
            return {
                "title": info.get("title", "Unknown Track"),
                "artist": info.get("uploader", "YouTube"),
                "cover": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "stream_url": audio_url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
