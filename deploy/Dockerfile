# Lightweight Python 3.11 Image - Optimized for Netcup 8GB VPS
FROM python:3.11-slim

# System utilities for image processing and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-tam \
    tesseract-ocr-hin \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Generate sample documents and seed 300 initial land records if DB doesn't exist
RUN python -m app.generate_samples && python -m app.seed_data

EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_server.py"]
