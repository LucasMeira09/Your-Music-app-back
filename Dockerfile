FROM python:3.10-slim

# On installe FFmpeg sur le système Linux de Render
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# On lance Uvicorn en utilisant le port dynamique exigé par Render ($PORT)
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
