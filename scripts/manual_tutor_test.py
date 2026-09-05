from src.db.database import SessionLocal
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge
from src.agents.difficulty_estimator import estimate_difficulty
from src.agents.tutor import generate_tutoring_content

db = SessionLocal()
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

set_mastery(db, "student_001", "linear_algebra", 0.9)
set_mastery(db, "student_001", "calculus", 0.2)  # weak -> should trigger redirect + easy difficulty

assessment_result = assess_knowledge(db, "student_001", "Explain backpropagation.", cg)
difficulty_estimate = estimate_difficulty(assessment_result)
tutor_response = generate_tutoring_content(cg, assessment_result, difficulty_estimate)

print(tutor_response.model_dump_json(indent=2))