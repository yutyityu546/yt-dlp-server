frofrom fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_id(url: str):
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else url

@app.get("/stream")
async def get_stream(url: str):
    video_id = extract_id(url)
    clean_url = f"https://www.youtube.com/watch?v={video_id}"

    title = "YouTube Track"
    artist = "Music"
    cover = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # Метаданные через oEmbed
        try:
            meta_res = await client.get(f"https://noembed.com/embed?url={clean_url}")
            if meta_res.status_code == 200:
                meta = meta_res.json()
                raw_title = meta.get("title", "")
                if " - " in raw_title:
                    parts = raw_title.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    title = raw_title
                    artist = meta.get("author_name", "YouTube")
        except Exception:
            pass

        # Рабочие публичные Invidious-ноды
        instances = [
            "https://inv.tux.pizza",
            "https://invidious.nerdvpn.de",
            "https://vid.puffyan.us",
            "https://invidious.jing.rocks"
        ]

        for inst in instances:
            try:
                r = await client.get(f"{inst}/api/v1/videos/{video_id}")
                if r.status_code == 200:
                    data = r.json()
                    formats = data.get("adaptiveFormats", [])
                    # Фильтруем чистый звук
                    audio_streams = [f for f in formats if f.get("type", "").startswith("audio/")]
                    if audio_streams:
                        # Берем поток с проксированием через ноду, чтобы обойти бан IP от Google
                        best_audio = audio_streams[-1]
                        raw_stream = best_audio.get("url")
                        
                        # Если ссылка локальная или закрыта — пускаем через прокси ноды
                        if not raw_stream.startswith("http"):
                            stream_url = f"{inst}{raw_stream}"
                        else:
                            stream_url = raw_stream

                        return {
                            "title": data.get("title", title),
                            "artist": data.get("author", artist),
                            "cover": cover,
                            "stream_url": stream_url
                        }
            except Exception:
                continue

    raise HTTPException(status_code=500, detail="Все ноды сейчас перегружены, попробуй через минуту")
