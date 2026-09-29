from typing import Optional, List, Dict
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.services.rag_service import rag_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["Chat"])

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User question about VVCE")
    session_id: Optional[str] = Field(None, description="Optional client session identifier")

class SourceItem(BaseModel):
    title: str
    url: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    sufficient_evidence: bool
    chunks_retrieved: int

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def chat_sync(request: Request, body: ChatRequest):
    """
    Standard synchronous query endpoint returning the grounded answer, verified source citations,
    and evidence sufficiency status.
    """
    try:
        result = rag_service.answer_query(body.query)
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceItem(**s) for s in result.get("sources", [])],
            sufficient_evidence=result.get("sufficient_evidence", True),
            chunks_retrieved=result.get("chunks_retrieved", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def chat_stream(request: Request, body: ChatRequest):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint for the web widget.
    Streams incremental tokens as they are produced, followed by citation payloads.
    """
    return StreamingResponse(
        rag_service.stream_query(body.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
