import pytest
from app.services.hybrid_search import HybridSearchEngine, tokenize
from app.services.rag_service import RAGService

def test_tokenization_and_bm25():
    engine = HybridSearchEngine()
    chunks = [
        {"id": "c1", "text": "Admissions for B.E. programs are based on KCET and COMEDK entrance exams.", "url": "https://vvce.ac.in/admissions/"},
        {"id": "c2", "text": "The Department of Mechanical Engineering has state of the art CAD CAM laboratories.", "url": "https://vvce.ac.in/mech/"},
    ]
    engine.index(chunks)

    # Search for acronym "KCET"
    results = engine.search_bm25("KCET", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "c1"

def test_reciprocal_rank_fusion():
    engine = HybridSearchEngine()
    dense_res = [
        {"id": "doc_a", "title": "Doc A"},
        {"id": "doc_b", "title": "Doc B"}
    ]
    sparse_res = [
        {"id": "doc_b", "title": "Doc B"},
        {"id": "doc_c", "title": "Doc C"}
    ]

    fused = engine.fuse_rrf(dense_res, sparse_res, rrf_k=60, top_n=3)
    assert len(fused) == 3
    # doc_b appears in both dense and sparse, so its RRF score should be highest
    assert fused[0]["id"] == "doc_b"

def test_evidence_sufficiency_gating():
    service = RAGService()

    # Empty chunks -> insufficient evidence
    assert service.check_evidence_sufficiency("What is the fee?", []) is False

    # Low similarity chunks below 0.65 -> insufficient evidence
    low_sim_chunks = [{"similarity": 0.42, "text": "Unrelated snippet"}]
    assert service.check_evidence_sufficiency("What is the fee?", low_sim_chunks) is False

    # High similarity chunks -> sufficient evidence
    high_sim_chunks = [{"similarity": 0.88, "text": "The annual fee is 100000"}]
    assert service.check_evidence_sufficiency("What is the fee?", high_sim_chunks) is True
