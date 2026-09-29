from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.core.security import verify_admin_key
from app.services.crawler import VVCEWebCrawler
from app.services.processor import DocumentProcessor
from app.services.vector_store import vector_store
from app.services.rag_service import rag_service

router = APIRouter(tags=["Ingestion & Admin"])

class IngestRequest(BaseModel):
    seed_urls: Optional[List[str]] = None
    max_pages: Optional[int] = 20
    clear_existing: Optional[bool] = False

def run_ingestion_pipeline(seed_urls: Optional[List[str]], max_pages: int, clear_existing: bool) -> dict:
    """Executes crawl, sanitize, chunk, embed, and index."""
    crawler = VVCEWebCrawler()
    raw_docs = crawler.crawl_urls(urls=seed_urls, max_pages=max_pages)

    processor = DocumentProcessor()
    chunks = processor.process_documents(raw_docs)

    if clear_existing:
        vector_store.clear()

    added_count = vector_store.add_chunks(chunks)
    rag_service.reload_bm25(chunks)

    return {
        "pages_crawled": len(raw_docs),
        "chunks_indexed": added_count,
        "total_in_vector_store": vector_store.count()
    }

@router.post("/ingest/trigger", dependencies=[Depends(verify_admin_key)])
def trigger_ingest(body: IngestRequest):
    """
    Admin-protected endpoint to trigger the web crawling and RAG re-indexing pipeline.
    Requires header: 'X-Admin-API-Key'.
    """
    try:
        stats = run_ingestion_pipeline(
            seed_urls=body.seed_urls,
            max_pages=body.max_pages or 20,
            clear_existing=body.clear_existing or False
        )
        return {
            "status": "success",
            "message": "Ingestion pipeline completed successfully.",
            "metrics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
