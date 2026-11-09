# Build context is the repository root (see docker-compose.yml), so the generated
# benchmark dataset can be baked into the image as seed data.
FROM python:3.12-slim

# FFmpeg for video pre-processing (CF-03)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY dataset/testcases.csv ./dataset/testcases.csv
COPY dataset/videos ./dataset/videos

ENV DATA_DIR=/app/data \
    DATASET_DIR=/app/dataset

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
