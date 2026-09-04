import json
import tempfile
from src.graph.concept_graph import ConceptGraph


def test_from_dataset_json_loads_correctly():
    sample = {
        "concepts": [
            {"id": "a", "name": "A", "domain": "Math", "description": ""},
            {"id": "b", "name": "B", "domain": "CS", "description": ""},
        ],
        "prerequisites": [{"prerequisite_id": "a", "concept_id": "b"}],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample, f)
        path = f.name

    cg = ConceptGraph.from_dataset_json(path)
    assert cg.get_learning_path("b") == ["a", "b"]
    assert cg.get_concepts_by_domain("Math") == ["a"]


def test_from_dataset_json_skips_cyclic_edge():
    sample = {
        "concepts": [
            {"id": "a", "name": "A", "domain": "Math", "description": ""},
            {"id": "b", "name": "B", "domain": "CS", "description": ""},
        ],
        "prerequisites": [
            {"prerequisite_id": "a", "concept_id": "b"},
            {"prerequisite_id": "b", "concept_id": "a"},  # cycle — should be skipped, not crash
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample, f)
        path = f.name

    cg = ConceptGraph.from_dataset_json(path)  # should not raise
    assert cg.get_direct_prerequisites("b") == ["a"]