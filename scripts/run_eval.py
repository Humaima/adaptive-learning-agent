import json
import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge
from src.agents.difficulty_estimator import estimate_difficulty

EVAL_CASES_PATH = "data/eval_cases.json"
REPORT_PATH = "data/eval_report.json"


def _fresh_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def run_eval():
    cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")
    cases = json.loads(Path(EVAL_CASES_PATH).read_text())

    results = []
    for case in cases:
        db = _fresh_db()
        for concept_id, mastery in case.get("mastery_setup", {}).items():
            set_mastery(db, "eval_student", concept_id, mastery)

        start = time.time()
        try:
            assessment = assess_knowledge(db, "eval_student", case["question"], cg)
            estimate = estimate_difficulty(assessment)
            error = None
        except Exception as e:
            assessment, estimate, error = None, None, str(e)
        latency = time.time() - start

        target_correct = assessment is not None and assessment.target_concept_id == case["expected_target_concept_id"]
        has_teach_next_expectation = "expected_teach_next" in case
        teach_next_correct = (
            estimate is not None and has_teach_next_expectation
            and estimate.concept_to_teach_next == case["expected_teach_next"]
        )

        results.append({
            "id": case["id"], "question": case["question"],
            "expected_target": case["expected_target_concept_id"],
            "actual_target": assessment.target_concept_id if assessment else None,
            "target_correct": target_correct,
            "expected_teach_next": case.get("expected_teach_next"),
            "actual_teach_next": estimate.concept_to_teach_next if estimate else None,
            "teach_next_correct": teach_next_correct if has_teach_next_expectation else None,
            "latency_seconds": round(latency, 2), "error": error,
        })

    total = len(results)
    target_accuracy = sum(r["target_correct"] for r in results) / total
    scored = [r for r in results if r["teach_next_correct"] is not None]
    teach_next_accuracy = sum(r["teach_next_correct"] for r in scored) / len(scored) if scored else None

    report = {
        "total_cases": total,
        "target_identification_accuracy": round(target_accuracy, 3),
        "teach_next_accuracy": round(teach_next_accuracy, 3) if teach_next_accuracy is not None else None,
        "average_latency_seconds": round(sum(r["latency_seconds"] for r in results) / total, 2),
        "failures": [r for r in results if not r["target_correct"] or r["teach_next_correct"] is False],
        "all_results": results,
    }
    Path(REPORT_PATH).write_text(json.dumps(report, indent=2))

    print(f"\n=== Eval Report ===\nTotal cases: {total}")
    print(f"Target identification accuracy: {target_accuracy:.1%}")
    if teach_next_accuracy is not None:
        print(f"Teach-next (redirect) accuracy: {teach_next_accuracy:.1%}")
    print(f"Average latency: {report['average_latency_seconds']}s")
    if report["failures"]:
        print(f"\n{len(report['failures'])} failing case(s):")
        for f in report["failures"]:
            print(f"  [{f['id']}] '{f['question']}'  expected={f['expected_target']} got={f['actual_target']}")
    print(f"\nFull report saved to {REPORT_PATH}")


if __name__ == "__main__":
    run_eval()