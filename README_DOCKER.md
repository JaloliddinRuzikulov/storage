# Storage Service - Docker Deployment

Centralized file management service for the Pixelfy ecosystem.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Create .env file (optional, has defaults)
cp .env.example .env
# Edit .env if needed

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Using Docker (Manual)

```bash
# Build image
docker build -t pixelfy-storage .

# Run container
docker run -d \
  --name pixelfy-storage \
  -p 9005:9005 \
  -e API_KEY=your_secret_key_here \
  -v storage_data:/app/data \
  pixelfy-storage

# View logs
docker logs -f pixelfy-storage

# Stop and remove
docker stop pixelfy-storage
docker rm pixelfy-storage
```

## Environment Variables

Create `.env` file (all optional with defaults):

```bash
# Server Configuration
HOST=0.0.0.0
PORT=9005
DEBUG=False

# Storage Settings
STORAGE_BASE_PATH=/app/data
MAX_FILE_SIZE=52428800  # 50MB

# Security
API_KEY=storage_service_secret_key_2024

# File Extensions (comma-separated)
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp,mp4,webm,mov,avi,mkv,mp3,wav,m4a,aac,pdf,pptx,ppt,docx,doc

# Cleanup Settings
AUTO_CLEANUP_ENABLED=True
CLEANUP_OLDER_THAN_DAYS=30
CLEANUP_INTERVAL_HOURS=24
```

## API Endpoints

Once running, service will be available at:

- **Base URL**: http://localhost:9005
- **API Docs**: http://localhost:9005/docs
- **Health Check**: http://localhost:9005/

### Upload File

```bash
curl -X POST "http://localhost:9005/upload" \
  -H "Authorization: Bearer storage_service_secret_key_2024" \
  -F "file=@image.jpg" \
  -F "service=web" \
  -F "folder=media"
```

### List Files

```bash
curl -X GET "http://localhost:9005/files?service=web&limit=10" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

### Serve File

```bash
curl "http://localhost:9005/serve/web/media/filename.jpg"
```

### Get Statistics

```bash
curl "http://localhost:9005/stats" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

### Cleanup Old Files

```bash
curl -X POST "http://localhost:9005/cleanup?days=30" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

## Volumes

- `storage_data:/app/data` - All uploaded and generated files

## Storage Organization

```
data/
├── web/           # Web application files
├── ai/            # AI service files
├── presentai/     # PresentAI service files
├── office/        # Office service files
├── uploads/       # General uploads
├── media/         # Media files
└── temp/          # Temporary files
```

## System Requirements

- **Docker**: 20.10+
- **RAM**: 512MB minimum (1GB recommended)
- **Disk**: 1GB for image + storage for files

## Troubleshooting

### Permission Issues

```bash
# Fix volume permissions
docker exec pixelfy-storage chown -R $(id -u):$(id -g) /app/data
```

### Container Won't Start

```bash
# Check logs
docker logs pixelfy-storage

# Rebuild image
docker-compose down
docker-compose up -d --build
```

### API Authentication Error

```bash
# Check API key
docker exec pixelfy-storage env | grep API_KEY

# Update API key
docker-compose down
# Edit .env file
docker-compose up -d
```

### Storage Full

```bash
# Check storage stats
curl "http://localhost:9005/stats" \
  -H "Authorization: Bearer storage_service_secret_key_2024"

# Clean up old files
curl -X POST "http://localhost:9005/cleanup?days=7" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

## Production Deployment

### With NGINX Reverse Proxy

Add to your NGINX config:

```nginx
server {
    listen 80;
    server_name storage.yourdomain.com;

    location / {
        proxy_pass http://localhost:9005;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        client_max_body_size 50M;
        proxy_read_timeout 300s;
    }
}
```

### Security

**IMPORTANT**: Never commit `.env` file with API keys to git!

```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Use strong API keys in production
STORAGE_API_KEY=$(openssl rand -hex 32)
```

### Backup Strategy

```bash
# Backup storage data
docker run --rm \
  -v storage_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/storage-backup-$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm \
  -v storage_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/storage-backup-20240101.tar.gz -C /
```

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python start.py
```

### Hot Reload

Mount source code for development:

```yaml
services:
  storage:
    volumes:
      - ./app:/app/app  # Mount source code
    command: uvicorn app.main:app --host 0.0.0.0 --port 9005 --reload
```

## Integration with Other Services

### Web Application

```env
# In web/.env
STORAGE_SERVICE_URL=http://localhost:9005
STORAGE_API_KEY=storage_service_secret_key_2024
```

### AI/PresentAI/Office Services

All services can use the storage service for file management:

```python
import requests

# Upload file
files = {"file": open("video.mp4", "rb")}
data = {"service": "ai", "folder": "outputs"}
headers = {"Authorization": "Bearer storage_service_secret_key_2024"}
response = requests.post(
    "http://localhost:9005/upload",
    files=files,
    data=data,
    headers=headers
)
```

## Features

- **Unified Storage**: Centralized file management for all services
- **Service Organization**: Automatic categorization by service
- **Authentication**: Bearer token protection
- **Auto Cleanup**: Configurable automatic file cleanup
- **Thumbnails**: Automatic thumbnail generation for images
- **Statistics**: Storage usage analytics
