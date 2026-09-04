from src.db.database import SessionLocal
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge
from src.agents.difficulty_estimator import estimate_difficulty

db = SessionLocal()
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

set_mastery(db, "student_001", "linear_algebra", 0.9)
set_mastery(db, "student_001", "calculus", 0.2)  # weak — should trigger a redirect

result = assess_knowledge(db, "student_001", "Explain backpropagation.", cg)
estimate = estimate_difficulty(result)

print("Assessment:")
print(result.model_dump_json(indent=2))
print("\nDifficulty Estimate:")
print(estimate.model_dump_json(indent=2))