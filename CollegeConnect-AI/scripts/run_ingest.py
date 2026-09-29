import os
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.api.ingest import run_ingestion_pipeline
from app.core.config import settings

def main():
    print("==================================================")
    print(" CollegeConnect AI - VVCE Ingestion & Vector Pipeline ")
    print("==================================================")

    stats = run_ingestion_pipeline(
        seed_urls=None,
        max_pages=15,
        clear_existing=True
    )

    print("\n[+] Ingestion Complete:")
    print(f"    - Pages Crawled: {stats['pages_crawled']}")
    print(f"    - Chunks Created & Indexed: {stats['chunks_indexed']}")
    print(f"    - Total Vector Store Chunks: {stats['total_in_vector_store']}")
    print(f"    - ChromaDB Location: {settings.CHROMA_PERSIST_DIR}")

if __name__ == "__main__":
    main()
