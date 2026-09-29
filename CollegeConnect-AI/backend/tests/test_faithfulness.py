import pytest
from app.services.rag_service import rag_service, STANDARD_REFUSAL_DISCLAIMER

def test_out_of_scope_refusal():
    # An out-of-scope query lacking evidence in VVCE records
    query = "What is the admission procedure for Harvard Medical School?"
    response = rag_service.answer_query(query)

    assert response["sufficient_evidence"] is False or response["answer"] == STANDARD_REFUSAL_DISCLAIMER
    assert "official VVCE records" in response["answer"]

def test_citation_integrity():
    # Test that valid responses contain citations properly formatted
    query = "What are the cutoff ranks?"
    response = rag_service.answer_query(query)

    sources = response.get("sources", [])
    for s in sources:
        assert "url" in s
        assert "vvce.ac.in" in s["url"]
