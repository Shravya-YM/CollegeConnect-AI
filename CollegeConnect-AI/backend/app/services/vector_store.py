import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingFunction:
    """Wrapper for Google Gemini embeddings."""
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.api_key = api_key
        self.model = model
        self.client = None
        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}")

    def __call__(self, input: List[str]) -> List[List[float]]:
        if not self.client:
            raise RuntimeError("Gemini client not initialized. GEMINI_API_KEY required.")
        
        embeddings = []
        for text in input:
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text
                )
                # Google genai returns embedding object with values
                if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                    embeddings.append(response.embedding.values)
                elif hasattr(response, "embeddings") and len(response.embeddings) > 0:
                    embeddings.append(response.embeddings[0].values)
                else:
                    embeddings.append(response)
            except Exception as e:
                logger.error(f"Error calling Gemini embed_content: {e}")
                raise e
        return embeddings

class VectorStoreManager:
    def __init__(self):
        self.persist_dir = settings.get_chroma_dir()
        self.collection_name = settings.COLLECTION_NAME
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = None
        self._init_collection()

    def _get_embedding_function(self):
        """Returns Gemini embedding function if API key is set, else default Chroma function."""
        if settings.GEMINI_API_KEY:
            try:
                return GeminiEmbeddingFunction(
                    api_key=settings.GEMINI_API_KEY,
                    model=settings.GEMINI_EMBEDDING_MODEL
                )
            except Exception as e:
                logger.warning(f"Could not initialize Gemini embeddings, using fallback: {e}")

        # Fallback local embedding
        from chromadb.utils import embedding_functions
        return embedding_functions.DefaultEmbeddingFunction()

    def _init_collection(self):
        emb_fn = self._get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Adds structured chunks to Chroma collection."""
        if not chunks:
            return 0

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "url": c.get("url", ""),
                "title": c.get("title", ""),
                "chunk_index": c.get("chunk_index", 0),
            }
            for c in chunks
        ]

        # Chroma handles batches automatically
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def search_dense(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Dense similarity search returning matched documents with normalized similarity score."""
        if self.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"]
        )

        output = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for idx in range(len(results["ids"][0])):
                doc_id = results["ids"][0][idx]
                doc_text = results["documents"][0][idx]
                metadata = results["metadatas"][0][idx] if results["metadatas"] else {}
                distance = results["distances"][0][idx] if results["distances"] else 1.0

                # In Chroma cosine space, distance is 1 - cosine_similarity
                similarity = max(0.0, min(1.0, 1.0 - distance))

                output.append({
                    "id": doc_id,
                    "text": doc_text,
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "distance": distance,
                    "similarity": similarity,
                })

        return output

    def count(self) -> int:
        """Returns total document count in vector store."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear(self):
        """Clears the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self._init_collection()

# Singleton instance
vector_store = VectorStoreManager()
