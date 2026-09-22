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
    clean_url = f"https://www.youtube.com/watch?v={video_id}"
    
    title = "YouTube Track"
    artist = "Music"
    cover = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Метаданные трека
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

        # Живые инстансы Cobalt API
        instances = [
            "https://api.cobalt.tools",
            "https://cobalt-api.kwiatekm.tokyo",
            "https://api.wuk.sh"
        ]

        payload = {
            "url": clean_url,
            "downloadMode": "audio",
            "audioFormat": "mp3"
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        for inst in instances:
            try:
                r = await client.post(f"{inst}/", json=payload, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    stream_url = data.get("url")
                    if stream_url:
                        return {
                            "title": title,
                            "artist": artist,
                            "cover": cover,
                            "stream_url": stream_url
                        }
            except Exception:
                continue

    raise HTTPException(status_code=500, detail="Ошибка получения аудиопотока через шлюз")
