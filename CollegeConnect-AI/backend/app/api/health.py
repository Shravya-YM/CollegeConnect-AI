from fastapi import APIRouter
from app.core.config import settings
from app.services.vector_store import vector_store

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    """
    Health check endpoint returning system status and indexed knowledge metrics.
    """
    doc_count = vector_store.count()
    has_api_key = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "college": settings.COLLEGE_NAME,
        "indexed_chunks": doc_count,
        "gemini_api_configured": has_api_key,
        "gemini_model": settings.GEMINI_MODEL,
        "vector_backend": "ChromaDB (Persistent)",
    }
