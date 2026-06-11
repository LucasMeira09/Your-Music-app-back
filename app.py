from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import yt_dlp
import uuid

# uvicorn app:app --host 0.0.0.0 --port 8000 --reload

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)

COOKIES_SRC = "/etc/secrets/cookies.txt"
COOKIES_DST = "/tmp/cookies.txt"

if os.path.exists(COOKIES_SRC):
    shutil.copy(COOKIES_SRC, COOKIES_DST)

class Download(BaseModel):
    music_name: str

def remove_files(file_path):
    try:
        if os.path.exists(file_path):
            files_list = os.listdir(file_path)
            for file in files_list:
                file_to_remove = os.path.join(file_path, file)
                if os.path.isfile(file_to_remove):
                    os.remove(file_to_remove)
    except Exception as e:
        print(f"Error removing file: {e}")

@app.get("/static/{file_name}")
async def get_file(file_name: str):
    file_path = os.path.join("downloads", file_name)

    if os.path.exists(file_path):


        return FileResponse(
            path=file_path, 
            media_type="audio/mpeg", 
            filename=file_name,
        )
    else:
        return {"error": "File not found"}

@app.post("/download")
async def download_music(music_name: Download):
    remove_files("downloads")

    personal_id = str(uuid.uuid4())[:8]

    path = "downloads"

    try:
        cookie_path = os.getenv("COOKIES_PATH", "/etc/secrets/cookies.txt")
    except Exception as e:
        cookie_path = None

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{path}/{personal_id}-%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        **(({'ffmpeg_location': 'ffmpeg.exe'}) if os.name == 'nt' else {}),
        'default_search': 'ytsearch1',
        'quiet': True,
        'no_playlist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web'],  # force le client web
            }
        },
        'sleep_interval': 2,       # pause entre les requêtes
        'max_sleep_interval': 5,
        'cookiefile': COOKIES_DST,  # chemin vers le fichier de cookies
        'no_write_to_cookie_file': True,  # ne pas écrire dans le fichier de cookies
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([music_name.music_name])

    new__music = next(f for f in os.listdir(path) if f.startswith(personal_id))

    base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
    download_url = f"{base_url}/static/{new__music}"

    return {
        "status": "success",
        "download_url": download_url,
        "filename": new__music
    }
