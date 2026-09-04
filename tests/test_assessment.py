import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db import repository as repo
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import Concept, ConceptIdentification
from src.agents import assessment


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def sample_graph():
    cg = ConceptGraph()
    for cid, name in [("linear_algebra", "Linear Algebra"), ("calculus", "Calculus"),
                       ("neural_networks", "Neural Networks"), ("backpropagation", "Backpropagation")]:
        cg.add_concept(Concept(id=cid, name=name, domain="Math/ML", description=name))
    cg.add_prerequisite("linear_algebra", "neural_networks")
    cg.add_prerequisite("calculus", "neural_networks")
    cg.add_prerequisite("neural_networks", "backpropagation")
    return cg


def test_mastery_to_status_thresholds():
    assert assessment.mastery_to_status(None) == assessment.MasteryStatus.UNKNOWN
    assert assessment.mastery_to_status(0.2) == assessment.MasteryStatus.NOT_MASTERED
    assert assessment.mastery_to_status(0.9) == assessment.MasteryStatus.MASTERED


def test_identify_target_concept_rejects_unknown_id(sample_graph):
    fake_result = {
        "parsed": ConceptIdentification(target_concept_id="not_a_real_concept", reasoning="oops")
    }
    with patch("src.agents.assessment.with_structured_output_retry", return_value=fake_result):
        with pytest.raises(ValueError):
            assessment.identify_target_concept("Explain backprop", sample_graph)


def test_assess_knowledge_end_to_end(db_session, sample_graph):
    repo.set_mastery(db_session, "student_001", "linear_algebra", 0.9)
    repo.set_mastery(db_session, "student_001", "calculus", 0.2)
    # neural_networks, backpropagation intentionally left unassessed

    fake_result = {
        "parsed": ConceptIdentification(target_concept_id="backpropagation", reasoning="direct match")
    }
    with patch("src.agents.assessment.with_structured_output_retry", return_value=fake_result):
        result = assessment.assess_knowledge(db_session, "student_001", "Explain backpropagation.", sample_graph)

    status_by_concept = {a.concept_id: a.status for a in result.assessments}
    assert status_by_concept["linear_algebra"] == assessment.MasteryStatus.MASTERED
    assert status_by_concept["calculus"] == assessment.MasteryStatus.NOT_MASTERED
    assert status_by_concept["neural_networks"] == assessment.MasteryStatus.UNKNOWN
    assert status_by_concept["backpropagation"] == assessment.MasteryStatus.UNKNOWN
    assert result.learning_path == ["linear_algebra", "calculus", "neural_networks", "backpropagation"]