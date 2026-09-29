import re
from typing import List, Dict, Any
from rank_bm25 import BM25Plus

def tokenize(text: str) -> List[str]:
    """Tokenizes text for BM25 keyword matching."""
    text = text.lower()
    return re.findall(r"\b[a-z0-9_\-\.]{2,}\b", text)

class HybridSearchEngine:
    def __init__(self):
        self.bm25: BM25Plus = None
        self.indexed_chunks: List[Dict[str, Any]] = []

    def index(self, chunks: List[Dict[str, Any]]):
        """Indexes chunks for BM25 sparse search."""
        self.indexed_chunks = chunks
        if not chunks:
            self.bm25 = None
            return

        corpus = [tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Plus(corpus)

    def search_bm25(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Performs sparse BM25 keyword search."""
        if not self.bm25 or not self.indexed_chunks:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        scored_pairs = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in scored_pairs:
            if score > 0:
                chunk = dict(self.indexed_chunks[idx])
                chunk["bm25_score"] = float(score)
                results.append(chunk)

        return results

    def fuse_rrf(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        rrf_k: int = 60,
        top_n: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Combines dense vector search and sparse BM25 search using Reciprocal Rank Fusion (RRF).
        RRF(d) = sum( 1 / (rrf_k + rank(d)) )
        """
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Dense ranks
        for rank, doc in enumerate(dense_results, 1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            doc_map[doc_id] = doc

        # Sparse ranks
        for rank, doc in enumerate(sparse_results, 1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # Sort by fused RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)

        fused = []
        for did in sorted_ids[:top_n]:
            item = dict(doc_map[did])
            item["rrf_score"] = scores[did]
            fused.append(item)

        return fused
