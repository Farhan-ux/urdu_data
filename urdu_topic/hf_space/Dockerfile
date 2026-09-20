# Dockerfile for HuggingFace Spaces — runs the Urdu News Scraper 24/7
# Uses Python 3.11 slim image, installs deps, runs app.py

FROM python:3.11-slim

# Install system deps (needed for lxml, requests, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .
COPY gui_app ./gui_app

# Create data dir (HF Spaces persistent storage is mounted at /data)
RUN mkdir -p /data/urdu_scrape/data
ENV PROJECT_DIR=/data/urdu_scrape
ENV AUTOSTART=1

# Expose Gradio port
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]
