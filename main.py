from fastapi import FastAPI, HTTPException
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
    
    # 1. Забираем метаданные трека без блокировок
    title = "YouTube Track"
    artist = "Music"
    cover = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            meta_res = await client.get(f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}")
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

        # 2. Быстрые публичные шлюзы потоков (не банятся Google)
        gateways = [
            f"https://pipedapi.kavin.rocks/streams/{video_id}",
            f"https://api.piped.privacydev.net/streams/{video_id}",
            f"https://pipedapi.tokhmi.xyz/streams/{video_id}"
        ]

        for gw in gateways:
            try:
                r = await client.get(gw)
                if r.status_code == 200:
                    data = r.json()
                    audio_streams = data.get("audioStreams", [])
                    if audio_streams:
                        # Берем лучший аудиопоток
                        audio_url = audio_streams[-1].get("url")
                        return {
                            "title": title,
                            "artist": artist,
                            "cover": cover,
                            "stream_url": audio_url
                        }
            except Exception:
                continue

    raise HTTPException(status_code=500, detail="Не удалось получить аудиопоток. Попробуй другую ссылку.")
