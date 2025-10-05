# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the Storage Service component.

## Project Overview

The Storage Service is a centralized file management system for the Pixelfy ecosystem. It provides unified storage, retrieval, and management of media files across all services (web, ai, presentai, office).

## Development Commands

### Service Management
```bash
# Start Storage service
python start.py  # Runs on port 8005

# Install dependencies
pip install -r requirements.txt

# Health check
curl http://localhost:8005/

# API documentation
# Visit: http://localhost:8005/docs
```

### API Testing
```bash
# Upload a file
curl -X POST "http://localhost:8005/upload" \
  -H "Authorization: Bearer storage_service_secret_key_2024" \
  -F "file=@image.jpg" \
  -F "service=web" \
  -F "folder=media"

# List files
curl -X GET "http://localhost:8005/files?service=web&limit=10" \
  -H "Authorization: Bearer storage_service_secret_key_2024"

# Serve a file
curl -X GET "http://localhost:8005/serve/web/media/image.jpg"

# Get storage statistics
curl -X GET "http://localhost:8005/stats" \
  -H "Authorization: Bearer storage_service_secret_key_2024"

# Cleanup old files
curl -X POST "http://localhost:8005/cleanup?days=30" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

## Code Architecture

### Core Components

1. **Storage Manager** (`app/src/core/storage_manager.py`):
   - Centralized file management
   - Unique file ID generation with SHA256 hashing
   - Automatic thumbnail generation for images
   - Service-based organization (web, ai, presentai, office)
   - File validation and size limits

2. **FastAPI Application** (`app/main.py`):
   - RESTful API endpoints for file operations
   - Authentication via Bearer token
   - CORS configuration for web integration
   - Background cleanup tasks

3. **Configuration** (`app/config.py`):
   - Environment variable management
   - Storage path configuration
   - File size and extension limits
   - Auto-cleanup settings

### API Endpoints

- `POST /upload` - Upload files with service organization
- `GET /file/{file_path}` - Download files by path
- `GET /serve/{file_path}` - Serve files for web display
- `DELETE /file/{file_path}` - Delete specific files
- `GET /files` - List files with filtering options
- `GET /stats` - Get storage statistics by service
- `POST /cleanup` - Manual cleanup of old files
- `GET /health` - Detailed health check

### Storage Organization

```
storage/data/
├── web/           # Web application files
│   ├── media/     # User uploaded media
│   ├── uploads/   # General uploads
│   └── temp/      # Temporary files
├── ai/            # AI service files
│   ├── models/    # AI model files
│   ├── outputs/   # Generated content
│   └── temp/      # Processing temp files
├── presentai/     # PresentAI service files
│   ├── outputs/   # Generated presentations
│   └── temp/      # Processing temp files
├── office/        # Office service files
│   ├── converted/ # Converted documents
│   └── temp/      # Processing temp files
└── temp/          # Global temporary files
```

### File Metadata Structure

Each stored file includes:
```json
{
  "file_id": "uuid",
  "original_filename": "user_filename.jpg",
  "stored_filename": "uuid.jpg",
  "file_path": "web/media/uuid.jpg",
  "public_url": "/storage/web/media/uuid.jpg",
  "file_size": 1024000,
  "file_hash": "sha256_hash",
  "mime_type": "image/jpeg",
  "service": "web",
  "folder": "media",
  "user_id": "optional_user_id",
  "thumbnail_path": "web/media/thumb_uuid.jpg",
  "uploaded_at": "2024-01-01T00:00:00Z",
  "expires_at": null
}
```

## Web Integration

The storage service integrates with the Pixelfy web application through API proxies:

1. **Upload Proxy** (`/web/src/app/api/storage/upload/route.ts`):
   - Forwards uploads to storage service
   - Transforms responses to match existing format
   - Handles authentication with storage API key

2. **Serve Proxy** (`/web/src/app/api/storage/serve/[...path]/route.ts`):
   - Proxies file serving requests
   - Adds caching headers for performance
   - Handles error responses

3. **Environment Configuration**:
   ```env
   STORAGE_SERVICE_URL=http://localhost:8005
   STORAGE_API_KEY=storage_service_secret_key_2024
   ```

## Key Features

### File Management
- **Unique IDs**: UUID-based file identification
- **Hash Verification**: SHA256 file integrity checking
- **Service Organization**: Automatic categorization by service
- **Folder Structure**: Hierarchical organization support
- **File Validation**: Extension and size limit enforcement

### Image Processing
- **Thumbnail Generation**: Automatic 300x300 thumbnails for images
- **Format Conversion**: Automatic RGB conversion for compatibility
- **Quality Optimization**: JPEG compression for thumbnail efficiency

### Security & Performance
- **API Authentication**: Bearer token protection for write operations
- **File Serving**: Public read access for media files
- **CORS Support**: Cross-origin requests for web integration
- **Caching**: HTTP cache headers for static files

### Maintenance
- **Auto Cleanup**: Configurable automatic file cleanup
- **Storage Stats**: Service-wise storage analytics
- **Health Monitoring**: Comprehensive health check endpoints
- **Background Tasks**: Non-blocking maintenance operations

## File Structure

```
storage/
├── app/
│   ├── src/
│   │   └── core/
│   │       └── storage_manager.py    # Core file management
│   ├── config.py                     # Configuration management
│   └── main.py                       # FastAPI application
├── data/                             # Storage directories (auto-created)
│   ├── web/
│   ├── ai/
│   ├── presentai/
│   ├── office/
│   └── temp/
├── requirements.txt                  # Python dependencies
├── .env                             # Environment configuration
├── start.py                         # Service starter
├── README.md                        # User documentation
└── CLAUDE.md                        # Development guidance
```

## Environment Configuration

```env
# Server configuration
HOST=0.0.0.0
PORT=8005
DEBUG=True

# Storage paths
STORAGE_BASE_PATH=./data

# File limits
MAX_FILE_SIZE=52428800  # 50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp,mp4,webm,mov,avi,mkv,mp3,wav,m4a,aac,pdf,pptx,ppt,docx,doc

# Security
API_KEY=storage_service_secret_key_2024

# Cleanup settings
AUTO_CLEANUP_ENABLED=True
CLEANUP_OLDER_THAN_DAYS=30
CLEANUP_INTERVAL_HOURS=24
```

## Integration Points

### With Web Application
- Upload proxy at `/api/storage/upload`
- File serving at `/api/storage/serve/[...path]`
- Seamless integration with existing upload workflows
- Compatible response format with legacy endpoints

### With Other Services
- AI service can store generated content
- PresentAI service stores presentation files
- Office service stores converted documents
- Shared access through consistent API

## Development Patterns

### Error Handling
- Comprehensive try-catch in all endpoints
- Proper HTTP status codes (400, 401, 404, 500)
- Detailed error messages for debugging
- Graceful fallback for file operations

### File Operations
- Atomic file operations with proper cleanup
- Path validation to prevent directory traversal
- File type validation based on extensions
- Size limits enforced before processing

### Performance Optimization
- Streaming file responses for large files
- Thumbnail caching for images
- HTTP cache headers for static content
- Background cleanup to prevent blocking

## Testing and Debugging

### Local Development
```bash
# Start service with debug mode
DEBUG=True python start.py

# Test upload
curl -X POST "http://localhost:8005/upload" \
  -H "Authorization: Bearer storage_service_secret_key_2024" \
  -F "file=@test.jpg" \
  -F "service=web"

# Check storage stats
curl "http://localhost:8005/stats" \
  -H "Authorization: Bearer storage_service_secret_key_2024"
```

### Service Health
- Monitor storage space usage via `/stats` endpoint
- Check service connectivity via `/health` endpoint
- Monitor file operations via service logs
- Verify cleanup operations are running

## Future Enhancements

- Cloud storage integration (S3, Google Cloud)
- CDN integration for global file delivery
- Advanced image processing and optimization
- Video thumbnail generation
- File version control and history
- Bulk file operations API
- Real-time storage usage monitoring
- File sharing and permissions system