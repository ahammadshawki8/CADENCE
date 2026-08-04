# Dockerfile for Hugging Face Spaces deployment
# Optimized for audio ML workloads (librosa + openSMILE + scikit-learn)

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run FastAPI with uvicorn
# Single worker for Spaces (no need for multiple workers with 16 GB RAM)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
