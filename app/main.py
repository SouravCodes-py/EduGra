from fastapi import FastAPI
from app.routes import upload

app = FastAPI(
    title="EduGra API",
    description="EduGra: Graph-based Multi-Agent System for Adaptive Learning",
    version="0.1.0"
)

app.include_router(upload.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "EduGra Knowledge Extraction",
        "endpoints": {
            "upload": "/upload",
            "docs": "/docs"
        }
    }
