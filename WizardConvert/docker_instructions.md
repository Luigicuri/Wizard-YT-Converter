# Docker Setup for WizardConvert

To run this YouTube to MP3/MP4 converter on your local machine using Docker, follow these steps:

## Step 1: Create docker-compose.yml
Create a file named `docker-compose.yml` with the following content:

```yaml
version: '3'

services:
  wizardconvert:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - ./temp_downloads:/app/temp_downloads
    environment:
      - SESSION_SECRET=your_secret_key_here
    restart: unless-stopped
```

## Step 2: Create Dockerfile
Create a file named `Dockerfile` with the following content:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the application files
COPY app.py .
COPY main.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY utils/ ./utils/

# Create temp directory for downloads
RUN mkdir -p /app/temp_downloads

# Install Python dependencies
RUN pip install --no-cache-dir flask==2.3.3 gunicorn==23.0.0 yt-dlp==2023.11.16 pytube==15.0.0 flask-sqlalchemy==3.1.1 psycopg2-binary==2.9.9 email-validator==2.1.0

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
```

## Step 3: Build and Run with Docker Compose
In the directory containing your project files and the Docker files you created above, run:

```bash
docker-compose up -d
```

This will build the Docker image and start the container. The application will be accessible at:

```
http://localhost:5000
```

## Step 4: Stop the Container
When you want to stop the application, run:

```bash
docker-compose down
```

## Notes:
- The temp_downloads folder is mounted as a volume, so downloaded files persist even when the container restarts
- You can change the SESSION_SECRET value in docker-compose.yml to a more secure string 
- FFmpeg is included in the container for audio/video conversion
- The application listens on port 5000 by default