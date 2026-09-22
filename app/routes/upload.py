import os
import tempfile
from fastapi import APIRouter, UploadFile, File
from app.agents.knowledge_extraction.extractor import extract_text
from app.agents.knowledge_extraction.llm_extract import extract_concepts
from app.agents.knowledge_extraction.embeddings import get_embedding
from app.graph.graph_writer import write_concepts

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"temp_{file.filename}")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
            
        text = extract_text(temp_path)
        data = extract_concepts(text)
        embeddings = {c["name"]: get_embedding(c["name"]) for c in data.get("concepts", [])}
        
        write_concepts(data, embeddings, subject="uploaded")
        return {
            "status": "ok",
            "filename": file.filename,
            "concepts_written": len(data.get("concepts", [])),
            "concepts": [c["name"] for c in data.get("concepts", [])]
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
