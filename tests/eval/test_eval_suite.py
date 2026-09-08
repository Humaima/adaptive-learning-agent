import os
import json
import pytest

from scripts.run_eval import run_eval

RUN_EVAL = os.getenv("RUN_EVAL") == "1"


@pytest.mark.skipif(not RUN_EVAL, reason="Makes real Groq API calls — set RUN_EVAL=1 to run")
def test_eval_suite_meets_minimum_accuracy():
    run_eval()
    report = json.loads(open("data/eval_report.json").read())
    assert report["target_identification_accuracy"] >= 0.8, (
        f"Concept identification accuracy dropped to {report['target_identification_accuracy']:.1%} "
        f"— check data/eval_report.json for failing cases."
    )