from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

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
        'format': 'ba/b',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                # Клиенты Android VR и TV Embedded обходят капчу ботов на дата-центрах
                'player_client': ['android_music', 'android_vr', 'tv_embedded'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.android.apps.youtube.music/6.20.51 (Linux; U; Android 14)'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info:
                # Берем рабочий аудиопоток
                formats = [f for f in info['formats'] if f.get('acodec') != 'none']
                if formats:
                    audio_url = formats[-1].get('url')

            if not audio_url:
                raise HTTPException(status_code=404, detail="Audio stream not found")

            return {
                "title": info.get("title", "Unknown Track"),
                "artist": info.get("uploader", "YouTube"),
                "cover": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "stream_url": audio_url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
