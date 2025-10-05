import os
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import mimetypes
import aiofiles
from PIL import Image

from app.config import config

class StorageManager:
    """Centralized storage management for all Pixelfy services"""

    def __init__(self):
        self.base_path = config.STORAGE_BASE_PATH
        self.max_file_size = config.MAX_FILE_SIZE
        self.allowed_extensions = config.ALLOWED_EXTENSIONS

    async def store_file(
        self,
        file_content: bytes,
        filename: str,
        service: str = "general",
        folder: str = "",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store a file and return metadata

        Args:
            file_content: Raw file bytes
            filename: Original filename
            service: Service name (web, ai, presentai, office)
            folder: Optional subfolder
            user_id: Optional user identifier

        Returns:
            Dictionary with file metadata
        """
        # Validate file
        self._validate_file(file_content, filename)

        # Generate unique file info
        file_id = str(uuid.uuid4())
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_ext = Path(filename).suffix.lower()

        # Create storage path structure
        storage_path = self._build_storage_path(service, folder, user_id)
        unique_filename = f"{file_id}{file_ext}"
        full_path = storage_path / unique_filename

        # Ensure directory exists
        storage_path.mkdir(parents=True, exist_ok=True)

        # Write file
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_content)

        # Generate thumbnail for images and videos
        thumbnail_path = None
        if self._is_image(filename):
            thumbnail_path = await self._generate_thumbnail(full_path, storage_path)
        elif self._is_video(filename):
            thumbnail_path = await self._generate_video_thumbnail(full_path, storage_path)

        # Create metadata
        metadata = {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": unique_filename,
            "file_path": str(full_path.relative_to(self.base_path)),
            "public_url": f"/storage/{service}/{folder}/{unique_filename}" if folder else f"/storage/{service}/{unique_filename}",
            "file_size": len(file_content),
            "file_hash": file_hash,
            "mime_type": mimetypes.guess_type(filename)[0],
            "service": service,
            "folder": folder,
            "user_id": user_id,
            "thumbnail_path": thumbnail_path,
            "uploaded_at": datetime.utcnow().isoformat(),
            "expires_at": None  # Can be set for temporary files
        }

        return metadata

    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content by path"""
        full_path = self.base_path / file_path

        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        full_path = self.base_path / file_path

        try:
            if full_path.exists():
                full_path.unlink()

                # Also delete thumbnail if it exists
                thumbnail_path = full_path.parent / f"thumb_{full_path.name}"
                if thumbnail_path.exists():
                    thumbnail_path.unlink()

                return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

        return False

    async def list_files(
        self,
        service: str = None,
        folder: str = None,
        user_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List files with optional filtering"""
        files = []
        search_path = self.base_path

        if service:
            search_path = search_path / service
            if folder:
                search_path = search_path / folder
                if user_id:
                    search_path = search_path / user_id

        if not search_path.exists():
            return files

        # Get all files recursively
        for file_path in search_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("thumb_"):
                try:
                    stat = file_path.stat()
                    relative_path = file_path.relative_to(self.base_path)

                    file_info = {
                        "file_path": str(relative_path),
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "mime_type": mimetypes.guess_type(file_path.name)[0],
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                    files.append(file_info)
                except Exception as e:
                    print(f"Error reading file info for {file_path}: {e}")
                    continue

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified_at"], reverse=True)

        # Apply pagination
        return files[offset:offset + limit]

    async def cleanup_old_files(self, days: int = None) -> Dict[str, int]:
        """Clean up old files"""
        if days is None:
            days = config.CLEANUP_OLDER_THAN_DAYS

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        total_size_freed = 0

        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    file_age = datetime.fromtimestamp(stat.st_mtime)

                    if file_age < cutoff_date:
                        file_size = stat.st_size
                        file_path.unlink()
                        deleted_count += 1
                        total_size_freed += file_size

                except Exception as e:
                    print(f"Error during cleanup of {file_path}: {e}")
                    continue

        return {
            "deleted_files": deleted_count,
            "size_freed_bytes": total_size_freed,
            "size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
        }

    def _validate_file(self, file_content: bytes, filename: str):
        """Validate file size and type"""
        if len(file_content) > self.max_file_size:
            raise ValueError(f"File size {len(file_content)} exceeds maximum {self.max_file_size}")

        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            raise ValueError(f"File extension '{file_ext}' not allowed")

    def _build_storage_path(self, service: str, folder: str, user_id: Optional[str]) -> Path:
        """Build storage directory path"""
        path = self.base_path / service

        if folder:
            path = path / folder

        if user_id:
            path = path / user_id

        return path

    def _is_image(self, filename: str) -> bool:
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
        return Path(filename).suffix.lower() in image_extensions

    def _is_video(self, filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v'}
        return Path(filename).suffix.lower() in video_extensions

    async def _generate_thumbnail(self, image_path: Path, storage_path: Path) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            thumbnail_filename = f"thumb_{image_path.name}"
            thumbnail_path = storage_path / thumbnail_filename

            # Generate thumbnail using Pillow
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Create thumbnail
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)

            return str(thumbnail_path.relative_to(self.base_path))

        except Exception as e:
            print(f"Error generating thumbnail for {image_path}: {e}")
            return None

    async def _generate_video_thumbnail(self, video_path: Path, storage_path: Path) -> Optional[str]:
        """Generate thumbnail for video using ffmpeg"""
        try:
            import subprocess
            import tempfile

            thumbnail_filename = f"thumb_{video_path.stem}.jpg"
            thumbnail_path = storage_path / thumbnail_filename

            # Use ffmpeg to extract frame at 1 second
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-ss', '00:00:01.000',  # Extract frame at 1 second
                '-vframes', '1',        # Extract only 1 frame
                '-y',                   # Overwrite output file
                '-vf', 'scale=300:300:force_original_aspect_ratio=decrease,pad=300:300:(ow-iw)/2:(oh-ih)/2:black',  # Scale and pad to 300x300
                str(thumbnail_path)
            ]

            # Run ffmpeg with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if result.returncode == 0 and thumbnail_path.exists():
                print(f"Successfully generated video thumbnail: {thumbnail_path}")
                return str(thumbnail_path.relative_to(self.base_path))
            else:
                print(f"ffmpeg failed for {video_path}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"ffmpeg timeout for {video_path}")
            return None
        except FileNotFoundError:
            print(f"ffmpeg not found - install ffmpeg to generate video thumbnails")
            return None
        except Exception as e:
            print(f"Error generating video thumbnail for {video_path}: {e}")
            return None

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "services": {}
        }

        for service_path in self.base_path.iterdir():
            if service_path.is_dir():
                service_stats = {
                    "files": 0,
                    "size_bytes": 0,
                    "folders": {}
                }

                for file_path in service_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            service_stats["files"] += 1
                            service_stats["size_bytes"] += file_size
                            stats["total_files"] += 1
                            stats["total_size_bytes"] += file_size
                        except:
                            continue

                service_stats["size_mb"] = round(service_stats["size_bytes"] / (1024 * 1024), 2)
                stats["services"][service_path.name] = service_stats

        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        stats["total_size_gb"] = round(stats["total_size_bytes"] / (1024 * 1024 * 1024), 2)

        return stats