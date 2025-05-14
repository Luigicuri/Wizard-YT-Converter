FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the application files
COPY requirements.txt .
COPY app.py .
COPY main.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY utils/ ./utils/

# Create temp directory for downloads
RUN mkdir -p /app/temp_downloads

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]