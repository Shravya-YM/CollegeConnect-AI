import os
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from app.core.config import settings, BASE_DIR
from app.services.rag_service import rag_service, STANDARD_REFUSAL_DISCLAIMER
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Evaluation"])

def load_benchmark_dataset() -> List[Dict[str, Any]]:
    """Loads the benchmark test cases."""
    benchmark_file = BASE_DIR / "tests" / "benchmark_data.json"
    if not os.path.exists(benchmark_file):
        raise FileNotFoundError(f"Benchmark file not found at {benchmark_file}")
    with open(benchmark_file, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation_suite() -> Dict[str, Any]:
    """
    Executes quantitative evaluation across:
    1. Retrieval Accuracy: Hit@1, Hit@3, Hit@5, MRR@5
    2. Refusal Specificity on Out-of-Scope queries
    3. Citation Precision
    4. Faithfulness / Grounding Score
    """
    dataset = load_benchmark_dataset()

    total_in_scope = 0
    total_out_of_scope = 0
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    mrr_sum = 0.0

    correct_refusals = 0
    valid_citations_count = 0
    total_citations_checked = 0
    faithful_answers = 0

    detailed_results = []

    for item in dataset:
        qid = item["id"]
        category = item["category"]
        query = item["query"]
        expected_url = item.get("expected_source_url")
        is_in_scope = item.get("is_in_scope", True)

        # 1. Evaluate Retrieval
        retrieved_chunks = rag_service.retrieve(query, top_k=5)
        retrieved_urls = [c.get("url", "") for c in retrieved_chunks]

        # 2. Evaluate Response
        response = rag_service.answer_query(query)
        answer = response["answer"]
        sources = response.get("sources", [])
        sufficient_evidence = response.get("sufficient_evidence", True)

        res_detail = {
            "id": qid,
            "category": category,
            "query": query,
            "is_in_scope": is_in_scope,
            "sufficient_evidence": sufficient_evidence,
            "retrieved_sources": retrieved_urls,
        }

        if is_in_scope:
            total_in_scope += 1

            # Hit@K and MRR computation
            rank = None
            if expected_url:
                for idx, u in enumerate(retrieved_urls, 1):
                    if expected_url.rstrip("/") in u or u.rstrip("/") in expected_url:
                        rank = idx
                        break

            if rank is not None:
                if rank <= 1:
                    hit_1 += 1
                if rank <= 3:
                    hit_3 += 1
                if rank <= 5:
                    hit_5 += 1
                mrr_sum += 1.0 / rank

            # Citation precision check: All cited URLs must start with https://vvce.ac.in
            cited_urls = [s["url"] for s in sources]
            if cited_urls:
                for cu in cited_urls:
                    total_citations_checked += 1
                    if "vvce.ac.in" in cu:
                        valid_citations_count += 1

            # Faithfulness check: Response is grounded and non-refusal
            if sufficient_evidence and answer != STANDARD_REFUSAL_DISCLAIMER:
                faithful_answers += 1

            res_detail["retrieval_rank"] = rank

        else:
            # Out-of-Scope / Adversarial query
            total_out_of_scope += 1
            # Must cleanly refuse and not fabricate
            refused = (not sufficient_evidence) or (STANDARD_REFUSAL_DISCLAIMER in answer)
            if refused:
                correct_refusals += 1
            res_detail["properly_refused"] = refused

        detailed_results.append(res_detail)

    # Compute aggregate percentages
    hit_1_pct = round((hit_1 / total_in_scope * 100), 2) if total_in_scope else 0.0
    hit_3_pct = round((hit_3 / total_in_scope * 100), 2) if total_in_scope else 0.0
    hit_5_pct = round((hit_5 / total_in_scope * 100), 2) if total_in_scope else 0.0
    mrr_score = round(mrr_sum / total_in_scope, 4) if total_in_scope else 0.0

    refusal_specificity = round((correct_refusals / total_out_of_scope * 100), 2) if total_out_of_scope else 100.0
    citation_precision = round((valid_citations_count / total_citations_checked * 100), 2) if total_citations_checked else 100.0
    faithfulness_score = round((faithful_answers / total_in_scope * 100), 2) if total_in_scope else 0.0

    return {
        "summary": {
            "total_benchmark_queries": len(dataset),
            "in_scope_queries": total_in_scope,
            "out_of_scope_queries": total_out_of_scope,
            "metrics": {
                "retrieval_hit_at_1": f"{hit_1_pct}%",
                "retrieval_hit_at_3": f"{hit_3_pct}%",
                "retrieval_hit_at_5": f"{hit_5_pct}%",
                "mean_reciprocal_rank_mrr5": mrr_score,
                "faithfulness_groundedness_score": f"{faithfulness_score}%",
                "refusal_specificity_out_of_scope": f"{refusal_specificity}%",
                "citation_precision": f"{citation_precision}%"
            },
            "status": "PASS" if hit_3_pct >= 80.0 and refusal_specificity == 100.0 else "REVIEW"
        },
        "details": detailed_results
    }

@router.post("/eval/run")
def trigger_evaluation():
    """
    Executes the full evaluation suite against the golden benchmark dataset.
    """
    try:
        report = run_evaluation_suite()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
