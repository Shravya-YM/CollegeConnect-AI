import os
import sys
import json
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.api.evaluation import run_evaluation_suite

def main():
    print("==================================================")
    print(" Running CollegeConnect AI Golden Benchmark Suite ")
    print(" Target: Vidyavardhaka College of Engineering (VVCE)")
    print("==================================================\n")

    report = run_evaluation_suite()
    summary = report["summary"]
    metrics = summary["metrics"]

    print("----------------- SCORECARD ----------------------")
    print(f" Total Benchmark Queries Evaluated: {summary['total_benchmark_queries']}")
    print(f" In-Scope Questions:               {summary['in_scope_queries']}")
    print(f" Out-of-Scope / Probe Questions:   {summary['out_of_scope_queries']}")
    print("--------------------------------------------------")
    print(f" Retrieval Hit@1:                  {metrics['retrieval_hit_at_1']}")
    print(f" Retrieval Hit@3:                  {metrics['retrieval_hit_at_3']}")
    print(f" Retrieval Hit@5:                  {metrics['retrieval_hit_at_5']}")
    print(f" Mean Reciprocal Rank (MRR@5):     {metrics['mean_reciprocal_rank_mrr5']}")
    print(f" Groundedness / Faithfulness:      {metrics['faithfulness_groundedness_score']}")
    print(f" Refusal Specificity (Out-of-Scope): {metrics['refusal_specificity_out_of_scope']}")
    print(f" Citation Precision:               {metrics['citation_precision']}")
    print("--------------------------------------------------")
    print(f" Benchmark Status:                 [{summary['status']}]")
    print("==================================================")

if __name__ == "__main__":
    main()
