from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, Path as FastAPIPath
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import uvicorn
from pathlib import Path
import io

from app.config import config
from app.src.core.storage_manager import StorageManager

# Initialize FastAPI app
app = FastAPI(
    title="Pixelfy Storage Service",
    description="Centralized storage service for all Pixelfy components",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Storage manager
storage = StorageManager()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for protected endpoints"""
    if not credentials or credentials.credentials != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials

@app.on_event("startup")
async def startup_event():
    """Initialize storage directories on startup"""
    print("🚀 Starting Pixelfy Storage Service...")
    print(f"📍 Host: {config.HOST}")
    print(f"🚪 Port: {config.PORT}")
    print(f"🔧 Debug: {config.DEBUG}")
    print(f"📁 Storage Base: {config.STORAGE_BASE_PATH}")
    print(f"💾 Max File Size: {config.MAX_FILE_SIZE / (1024*1024):.1f}MB")

    config.create_directories()
    print("============================================================")

@app.get("/")
async def health_check():
    """Health check endpoint"""
    stats = await storage.get_storage_stats()
    return {
        "status": "healthy",
        "service": "Pixelfy Storage Service",
        "version": "1.0.0",
        "storage_stats": stats
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    service: str = Query("general", description="Service name (web, ai, presentai, office)"),
    folder: str = Query("", description="Optional subfolder"),
    user_id: Optional[str] = Query(None, description="Optional user identifier"),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Upload a file to storage"""
    try:
        # Read file content
        file_content = await file.read()

        # Store file
        metadata = await storage.store_file(
            file_content=file_content,
            filename=file.filename,
            service=service,
            folder=folder,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "file": metadata
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/file/{file_path:path}")
async def get_file(file_path: str):
    """Download a file by path"""
    try:
        file_content = await storage.get_file(file_path)

        if file_content is None:
            raise HTTPException(status_code=404, detail="File not found")

        # Get filename from path
        filename = Path(file_path).name

        # Create streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

@app.get("/serve/{file_path:path}")
async def serve_file(file_path: str):
    """Serve a file directly (for web display)"""
    try:
        full_path = config.STORAGE_BASE_PATH / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(full_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")

@app.delete("/file/{file_path:path}")
async def delete_file(
    file_path: str,
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Delete a file"""
    try:
        success = await storage.delete_file(file_path)

        if not success:
            raise HTTPException(status_code=404, detail="File not found or deletion failed")

        return {
            "success": True,
            "message": "File deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@app.get("/files")
async def list_files(
    service: Optional[str] = Query(None, description="Filter by service"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, description="Maximum number of files to return"),
    offset: int = Query(0, description="Number of files to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """List files with optional filtering"""
    try:
        files = await storage.list_files(
            service=service,
            folder=folder,
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "files": files,
            "count": len(files),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/stats")
async def get_storage_stats(
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Get storage statistics"""
    try:
        stats = await storage.get_storage_stats()
        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/cleanup")
async def cleanup_old_files(
    days: Optional[int] = Query(None, description="Delete files older than N days"),
    credentials: HTTPAuthorizationCredentials = Depends(verify_api_key)
):
    """Clean up old files"""
    try:
        result = await storage.cleanup_old_files(days)

        return {
            "success": True,
            "message": "Cleanup completed",
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@app.get("/health")
async def detailed_health():
    """Detailed health check"""
    try:
        stats = await storage.get_storage_stats()

        health_info = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Use actual timestamp
            "version": "1.0.0",
            "storage": {
                "base_path": str(config.STORAGE_BASE_PATH),
                "total_files": stats["total_files"],
                "total_size_mb": stats["total_size_mb"],
                "services": list(stats["services"].keys())
            },
            "config": {
                "max_file_size_mb": config.MAX_FILE_SIZE / (1024 * 1024),
                "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
                "auto_cleanup": config.AUTO_CLEANUP_ENABLED
            }
        }

        return health_info

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        reload_dirs=["app"] if config.DEBUG else None
    )