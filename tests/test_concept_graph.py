import pytest
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import Concept


@pytest.fixture
def simple_graph():
    cg = ConceptGraph()
    for cid, name in [("a", "A"), ("b", "B"), ("c", "C")]:
        cg.add_concept(Concept(id=cid, name=name))
    cg.add_prerequisite("a", "b")
    cg.add_prerequisite("b", "c")
    return cg


def test_direct_prerequisites(simple_graph):
    assert simple_graph.get_direct_prerequisites("c") == ["b"]


def test_all_prerequisites_ordered(simple_graph):
    assert simple_graph.get_all_prerequisites("c") == ["a", "b"]


def test_learning_path(simple_graph):
    assert simple_graph.get_learning_path("c") == ["a", "b", "c"]


def test_cycle_detection(simple_graph):
    with pytest.raises(ValueError):
        simple_graph.add_prerequisite("c", "a")  # would create a -> b -> c -> a cycle


def test_missing_concept_raises(simple_graph):
    with pytest.raises(ValueError):
        simple_graph.add_prerequisite("a", "nonexistent")