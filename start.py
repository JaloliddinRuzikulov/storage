#!/usr/bin/env python3
"""
Pixelfy Storage Service Starter
"""
import uvicorn
from app.config import config

if __name__ == "__main__":
    print("🚀 Starting Pixelfy Storage Service...")
    print(f"📍 Host: {config.HOST}")
    print(f"🚪 Port: {config.PORT}")
    print(f"🔧 Debug: {config.DEBUG}")
    print(f"📁 Storage Base: {config.STORAGE_BASE_PATH}")

    print("\n🌐 Service will be available at:")
    print(f"   • API: http://{config.HOST}:{config.PORT}")
    print(f"   • Docs: http://{config.HOST}:{config.PORT}/docs")
    print(f"   • ReDoc: http://{config.HOST}:{config.PORT}/redoc")

    print("\n🎯 Example usage:")
    print(f"   curl -X POST \"http://{config.HOST}:{config.PORT}/upload\" \\")
    print(f"     -H \"Authorization: Bearer {config.API_KEY}\" \\")
    print(f"     -F \"file=@image.jpg\" \\")
    print(f"     -F \"service=web\" \\")
    print(f"     -F \"folder=media\"")

    print("\n============================================================")

    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        reload_dirs=["app"] if config.DEBUG else None
    )