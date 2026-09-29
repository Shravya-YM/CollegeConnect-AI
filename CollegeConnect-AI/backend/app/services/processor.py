import os
import re
import json
import hashlib
from app.core.config import settings

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Recursively chunks text by headers, paragraphs, and sentence boundaries.
    """
    if not text:
        return []

    # First split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph exceeds chunk size and current_chunk isn't empty, flush
        if len(current_chunk) + len(para) > chunk_size and len(current_chunk) >= (chunk_size - overlap):
            chunks.append(current_chunk.strip())
            # Maintain overlap with the end of current_chunk
            overlap_prefix = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
            current_chunk = overlap_prefix + " " + para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

class DocumentProcessor:
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_documents(self, documents: list[dict]) -> list[dict]:
        """
        Takes raw crawled documents and produces structured, contextual chunks with metadata.
        """
        processed_chunks = []

        for doc in documents:
            url = doc.get("url", "")
            title = doc.get("title", "")
            full_text = doc.get("text", "")

            # Segment into chunks
            raw_chunks = chunk_text(full_text, self.chunk_size, self.overlap)

            for i, raw_chunk in enumerate(raw_chunks):
                # Generate unique stable hash ID for chunk
                chunk_id = hashlib.md5(f"{url}_{i}_{raw_chunk[:50]}".encode()).hexdigest()

                # Add breadcrumb header to assist embedding and retrieval context
                context_prefix = f"Context: [VVCE Official Website > {title}]\nSource URL: {url}\n---\n"
                enriched_chunk_text = context_prefix + raw_chunk

                processed_chunks.append({
                    "id": chunk_id,
                    "url": url,
                    "title": title,
                    "chunk_index": i,
                    "text": enriched_chunk_text,
                    "raw_content": raw_chunk,
                })

        # Save processed chunks
        output_file = os.path.join(settings.PROCESSED_DATA_DIR, "chunks.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(processed_chunks, f, indent=2, ensure_ascii=False)

        return processed_chunks
