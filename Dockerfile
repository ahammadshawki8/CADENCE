# Cadence web app — Hugging Face Spaces (Docker SDK) / local container.
FROM python:3.11-slim

WORKDIR /app

# libsndfile for soundfile/librosa; ffmpeg as a decode fallback.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt ./app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY . .

# Hugging Face Spaces expects the app on port 7860.
EXPOSE 7860
CMD ["uvicorn", "app.backend:app", "--host", "0.0.0.0", "--port", "7860"]
