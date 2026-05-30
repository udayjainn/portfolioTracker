# Build from repository root:
#   docker build -f pipeline/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ .
COPY backend/app/models ./app/models
COPY backend/app/database.py ./app/database.py
