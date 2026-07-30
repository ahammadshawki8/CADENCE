# Cadence backend API - container image (optional; Render can also run native Python).
FROM python:3.12-slim

WORKDIR /app

# libsndfile for soundfile/librosa; ffmpeg as a decode fallback.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
