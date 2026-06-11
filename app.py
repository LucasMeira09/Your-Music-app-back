from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import uuid
import subprocess
import glob

# uvicorn app:app --host 0.0.0.0 --port 8000 --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)

class Download(BaseModel):
    music_name: str

def remove_files(path):
    for f in glob.glob(f"{path}/*"):
        try:
            os.remove(f)
        except:
            pass

@app.get("/static/{file_name}")
async def get_file(file_name: str):
    file_path = os.path.join("downloads", file_name)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type="audio/mpeg", filename=file_name)
    return {"error": "File not found"}

@app.post("/download")
async def download_music(music_name: Download):
    remove_files("downloads")

    try:
        result = subprocess.run(
            ["spotdl", "download", music_name.music_name, "--output", "downloads/{title}"],
            capture_output=True, text=True, timeout=120
        )

        files = glob.glob("downloads/*.mp3")
        if not files:
            return {"status": "error", "message": result.stderr or "Fichier introuvable"}

        file_name = os.path.basename(files[0])
        base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")

        return {
            "status": "success",
            "download_url": f"{base_url}/static/{file_name}",
            "filename": file_name
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout — téléchargement trop long"}
    except Exception as e:
        return {"status": "error", "message": str(e)}