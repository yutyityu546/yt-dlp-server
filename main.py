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
    # Притворяемся Android-клиентом YouTube, чтобы обойти капчу ботов
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Ищем прямую ссылку на аудио
            audio_url = None
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info:
                # Фильтруем чистые аудиоформаты
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if audio_formats:
                    audio_url = audio_formats[-1].get('url')
                else:
                    audio_url = info['formats'][-1].get('url')

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
